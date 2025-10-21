document.addEventListener('DOMContentLoaded', () => {

    // ========== 自定义确认对话框 ==========
    function showConfirmDialog(title, message, fileInfo = null) {
        return new Promise((resolve) => {
            // 移除现有对话框
            const existingDialog = document.getElementById('confirm-dialog-overlay');
            if (existingDialog) {
                existingDialog.remove();
            }

            const dialogHtml = `
                <div id="confirm-dialog-overlay" class="confirm-dialog-overlay">
                    <div class="confirm-dialog">
                        <div class="confirm-dialog-header">
                            <h3 class="confirm-dialog-title">${escapeHtml(title)}</h3>
                        </div>
                        <div class="confirm-dialog-content">
                            ${fileInfo ? `
                                <div class="confirm-file-info">
                                    <div class="confirm-file-name">${escapeHtml(fileInfo.name)}</div>
                                    <div class="confirm-file-size">${escapeHtml(fileInfo.size)}</div>
                                </div>
                            ` : ''}
                            <p class="confirm-dialog-message">${escapeHtml(message)}</p>
                        </div>
                        <div class="confirm-dialog-actions">
                            <button class="confirm-cancel-btn" type="button">Cancel</button>
                            <button class="confirm-delete-btn" type="button">Delete</button>
                        </div>
                    </div>
                </div>
            `;

            document.body.insertAdjacentHTML('beforeend', dialogHtml);
            const overlay = document.getElementById('confirm-dialog-overlay');

            // 使用事件委托，避免复杂的事件绑定
            const handleClick = (e) => {
                // 检查点击的是取消按钮
                if (e.target.classList.contains('confirm-cancel-btn')) {
                    e.stopPropagation();
                    e.preventDefault();
                    resolve(false);
                    overlay.remove();
                    return;
                }

                // 检查点击的是删除按钮
                if (e.target.classList.contains('confirm-delete-btn')) {
                    e.stopPropagation();
                    e.preventDefault();
                    resolve(true);
                    overlay.remove();
                    return;
                }

                // 检查点击的是外部区域
                if (e.target === overlay) {
                    resolve(false);
                    overlay.remove();
                    return;
                }
            };

            // 直接在按钮上添加事件监听器作为备用方案
            const cancelBtn = overlay.querySelector('.confirm-cancel-btn');
            const deleteBtn = overlay.querySelector('.confirm-delete-btn');

            if (cancelBtn) {
                cancelBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    resolve(false);
                    overlay.remove();
                });
            }

            if (deleteBtn) {
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    resolve(true);
                    overlay.remove();
                });
            }

            // ESC键关闭
            const handleKeydown = (e) => {
                if (e.key === 'Escape') {
                    resolve(false);
                    overlay.remove();
                }
            };

            // 使用事件委托，在overlay上监听所有点击
            overlay.addEventListener('click', handleClick);
            document.addEventListener('keydown', handleKeydown);

            // 清理事件监听器
            const cleanup = () => {
                overlay.removeEventListener('click', handleClick);
                document.removeEventListener('keydown', handleKeydown);
            };

            // 对话框移除时清理
            overlay.addEventListener('animationend', cleanup, { once: true });
        });
    }

    // ========== 移动端键盘处理 ==========
    function setupMobileKeyboardHandling() {
        if (window.visualViewport) {
            const inputContainer = document.querySelector('.input-container');
            const chatContainer = document.getElementById('chatContainer');

            const syncKeyboardGap = () => {
                const offset = window.innerHeight - window.visualViewport.height;
                if (offset > 0) {
                    // 键盘弹出时，调整输入框位置
                    inputContainer.style.transform = `translateY(-${offset}px)`;
                    // 确保聊天内容可见
                    chatContainer.style.marginBottom = `${offset + 60}px`;
                } else {
                    // 键盘收起时，恢复原状
                    inputContainer.style.transform = '';
                    chatContainer.style.marginBottom = '60px';
                }
            };

            window.visualViewport.addEventListener('resize', syncKeyboardGap);
            window.visualViewport.addEventListener('scroll', syncKeyboardGap);

            // 初始调用一次
            syncKeyboardGap();
        }
    }

    // ========== 配置区域 ==========
    const HOST_AGENT = 'chat/stream';
    const USER_INFO = 'user/me';
    const SESSIONS = 'session/uid/'
    const MESSAGES = 'session/msgs/'
    const PERSONAS = 'user/persona/'
    let sessionKey = generateSessionKey(); // 生成会话ID
    let currentTokenInfo = null;
    let isSending = false; //防抖

    // ========== DOM 元素获取 ==========
    const chatContainer = document.getElementById('chatContainer');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const errorDiv = document.getElementById('errorMessage');
    const menuIcon = document.getElementById('menu-icon');
    const settingsPanel = document.getElementById('settings-panel');
    const closeSettingsBtn = document.getElementById('close-settings');
    const overlay = document.getElementById('overlay');
    const themeToggleSwitch = document.getElementById('theme-toggle-switch');
    const loginWrapper = document.getElementById('loginWrapper');
    const userInfoContainer = document.getElementById('userInfo');
    const userNameEl = document.getElementById('userName');
    const loginReminder = document.getElementById('loginReminder');
    const logoutButton = document.getElementById('logoutButton');
    const sessionMenu = document.getElementById('session-menu');
    const sessionMenuHeader = document.querySelector('[data-target="session-menu"]');
    const personaMenu = document.getElementById('persona-menu');
    const personaMenuHeader = document.querySelector('[data-target="persona-menu"]');
    const filesMenu = document.getElementById('files-menu');
    const filesMenuHeader = document.querySelector('[data-target="files-menu"]');

    // ========== 工具函数 ==========
    // 生成随机会话ID
    function generateSessionKey() {
        const timestamp = Date.now();
        const random = Math.random().toString(36).slice(2, 11);
        const fingerprint = navigator.userAgent + navigator.language + screen.width + screen.height;
        const hash = btoa(fingerprint).slice(0, 8);
        return `session_${timestamp}_${random}_${hash}`;
    }

    // 设置菜单图标状态的辅助函数
    function setMenuIconState(menuHeader, isLoading) {
        const arrow = menuHeader.querySelector('.menu-arrow');
        const existingSpinner = menuHeader.querySelector('.loading-spinner');

        if (isLoading) {
            // 移除箭头，添加loading spinner
            if (arrow) arrow.style.display = 'none';
            if (!existingSpinner) {
                const spinner = document.createElement('div');
                spinner.className = 'loading-spinner';
                menuHeader.appendChild(spinner);
            }
        } else {
            // 移除loading spinner，显示箭头
            if (existingSpinner) existingSpinner.remove();
            if (arrow) arrow.style.display = '';
        }
    }

    function updateTokenInfo() {
        const keys = ['access_token', 'token'];
        for (const key of keys) {
            const token = localStorage.getItem(key);
            if (token) {
                currentTokenInfo = { key, token };
                return;
            }
        }
        currentTokenInfo = null;
    }

    // 显示错误信息
    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }

    // Persona专用的错误提示方法
    function personaShowError(message) {
        const saveBtn = document.getElementById('save-persona');
        if (saveBtn) {
            // 保存原始状态
            const originalText = saveBtn.textContent;
            const originalBgColor = saveBtn.style.backgroundColor;
            const originalDisabled = saveBtn.disabled;

            // 设置错误状态
            saveBtn.textContent = message;
            saveBtn.style.backgroundColor = '#ff4444';
            saveBtn.disabled = true;

            // 3秒后恢复
            setTimeout(() => {
                saveBtn.textContent = originalText;
                saveBtn.style.backgroundColor = originalBgColor;
                saveBtn.disabled = originalDisabled;
            }, 3000);
        }
    }

    // Persona专用的成功提示方法
    function personaShowSuccess(message) {
        const saveBtn = document.getElementById('save-persona');
        if (saveBtn) {
            // 保存原始状态
            const originalText = saveBtn.textContent;
            const originalBgColor = saveBtn.style.backgroundColor;
            const originalDisabled = saveBtn.disabled;

            // 设置成功状态
            saveBtn.textContent = message;
            saveBtn.style.backgroundColor = '#4CAF50';
            saveBtn.disabled = true;

            // 立即关闭模态框并刷新列表
            const modal = document.getElementById('persona-modal');
            if (modal) {
                modal.remove();
            }
            loadPersonaSettings(); // 刷新列表
        }
    }

    // ========== UI 操作函数 ==========
    function addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
        if (!isUser) {
            // 使用 marked 解析 Markdown
            const htmlContent = marked.parse(content);
            messageDiv.innerHTML = htmlContent;
            // 对代码块进行语法高亮
            messageDiv.querySelectorAll('pre code').forEach((block) => {
                Prism.highlightElement(block);
            });
        } else {
            messageDiv.innerHTML = content.replace(/\n/g, '<br>');
        }
        chatContainer.appendChild(messageDiv);
        // 滚动到底部
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return messageDiv;
    }
    // 设置发送按钮状态
    function setSendButtonState(enabled) {
        sendButton.disabled = !enabled;
        sendButton.textContent = enabled ? '🚀' : '⏳';
    }

    // ========== 核心功能：发送消息并处理流式响应 ==========
    async function sendMessage() {
        if (isSending) return;
        isSending = true;
        const message = messageInput.value.trim();
        if (!message) {
            showError('Message cannot be empty!');
            isSending = false;
            showError('请输入消息');
            return;
        }

        addMessage(message, true);
        messageInput.value = '';
        setSendButtonState(false);

        const aiMessageDiv = addMessage('', false);
        aiMessageDiv.classList.add('loading');

        try {
            const response = await fetch(HOST_AGENT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': currentTokenInfo ? `Bearer ${currentTokenInfo.token}` : null,

                },
                body: JSON.stringify({
                    instruction: message,
                    session_id: sessionKey,
                    user_id: currentTokenInfo ? await getUserId() : null
                })
            });

            if (!response.ok) {
                throw new Error(`服务器错误: ${response.status}`);

            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let isFirstChunk = true;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                const parts = buffer.split('\n\n');
                buffer = parts.pop();

                for (const part of parts) {
                    if (part.startsWith('data:')) {
                        const data = part.substring(5).trim();
                        if (!data) continue;

                        try {
                            const jsonObj = JSON.parse(data);

                            if (jsonObj.chunk && jsonObj.chunk.content) {
                                if (isFirstChunk) {
                                    aiMessageDiv.classList.remove('loading');
                                    isFirstChunk = false;
                                }
                                const textContent = jsonObj.chunk.content
                                    .filter(item => item.type === 'text')
                                    .map(item => item.text)
                                    .join('');
                                if (textContent) {
                                    // 使用 marked 解析 Markdown
                                    const htmlContent = marked.parse(textContent);
                                    aiMessageDiv.innerHTML = htmlContent;
                                    // 对代码块进行语法高亮
                                    aiMessageDiv.querySelectorAll('pre code').forEach((block) => {
                                        Prism.highlightElement(block);
                                    });
                                }
                            } else if (jsonObj.input_tokens !== undefined && jsonObj.time !== undefined) {
                                const elapsedTime = parseFloat(jsonObj.time).toFixed(2);

                                const statsDiv = document.createElement('div');
                                statsDiv.className = 'stats-container';
                                statsDiv.innerHTML = `
                                    <span>Time: ${elapsedTime}s</span>
                                    <span>In: ${jsonObj.input_tokens}</span>
                                    <span>Out: ${jsonObj.output_tokens}</span>
                                `;

                                aiMessageDiv.parentNode.insertBefore(statsDiv, aiMessageDiv.nextSibling);
                                // console.log("Usage Info from backend:", jsonObj);
                            }
                        } catch (e) {
                            console.error('解析SSE数据失败:', e, '原始数据:', data);
                        }
                    }
                }
            }
            if (isFirstChunk) {
                aiMessageDiv.classList.remove('loading');
            }
            if (!aiMessageDiv.textContent) {
                aiMessageDiv.textContent = '(无响应)';
            }
        } catch (error) {
            console.error('发送消息失败:', error);
            aiMessageDiv.classList.remove('loading');
            aiMessageDiv.textContent = '发送失败，请重试';
            showError('网络错误: ' + error.message);
        } finally {
            isSending = false;  // 确保无论如何都会重置状态
            setSendButtonState(true);
            messageInput.focus();
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }

    // 用户基本信息
    async function getUserId() {
        try {
            const res = await fetch(USER_INFO, {
                headers: {
                    'Accept': 'application/json',
                    'Authorization': `Bearer ${currentTokenInfo.token}`,
                },
            });

            if (res.ok) {
                const userData = await res.json();
                return userData.id;
            }
        } catch (error) {
            console.error('获取用户ID失败:', error);
        }
        return null;
    }

    // 获取会话列表
    async function loadChatSessions() {
        if (!currentTokenInfo) return;

        try {
            // 测试用延迟 - 2秒钟
            // await new Promise(resolve => setTimeout(resolve, 2000));

            const response = await fetch(`${SESSIONS}${await getUserId()}`, {
                headers: {
                    'Accept': 'application/json',
                    'Authorization': `Bearer ${currentTokenInfo.token}`
                }
            });

            const sessionList = document.querySelector('.session-list');
            sessionList.innerHTML = '';

            // 始终显示"创建新会话"选项
            const newSessionItem = document.createElement('div');
            newSessionItem.className = 'session-item new-session-item';
            newSessionItem.innerHTML = `
            <div class="session-preview new-session-preview">➕ New chat session</div>
        `;
            newSessionItem.addEventListener('click', () => {
                sessionKey = generateSessionKey(); // 生成新的会话ID
                chatContainer.innerHTML = ''; // 清空聊天内容
                closePanel(); // 关闭设置面板
            });
            sessionList.appendChild(newSessionItem);

            if (!response.ok) {
                // 即使获取历史会话失败，也显示"创建新会话"选项
                return;
            }

            const sessions = await response.json();
            // 添加历史会话
            sessions.forEach(session => {
                const sessionItem = document.createElement('div');
                sessionItem.className = 'session-item';
                sessionItem.innerHTML = `
                <div class="session-time">${formatTimestamp(session.updated_at)}</div>
                <div class="session-preview">${session.last_msg || 'No messages'}</div>
                <div class="view-chat-icon">
                    <svg viewBox="0 0 24 24">
                        <path d="M9 5v2h6.59L4 18.59 5.41 20 17 8.41V15h2V5z"/>
                    </svg>
                </div>
            `;
                sessionItem.setAttribute('data-session-id', session.id);
                sessionItem.setAttribute('data-session-key', session.session_key);
                sessionList.appendChild(sessionItem);

                sessionItem.addEventListener('click', async function () {

                    const sessionId = this.getAttribute('data-session-id');
                    const sKey = this.getAttribute('data-session-key');
                    try {
                        const response = await fetch(`${MESSAGES}${sessionId}`, {
                            headers: {
                                'Accept': 'application/json',
                                'Authorization': `Bearer ${currentTokenInfo.token}`,
                            }
                        });
                        if (response.ok) {
                            const messages = await response.json();
                            // 清空当前聊天内容
                            chatContainer.innerHTML = '';
                            // 渲染历史消息
                            messages.forEach(msg => {
                                const messageDiv = addMessage(msg.content, msg.role === 'user');
                                if (!msg.isUser && (msg.input_tokens || msg.output_tokens || msg.response_time)) {
                                    const statsDiv = document.createElement('div');
                                    statsDiv.className = 'stats-container';
                                    const elapsedTime = msg.response_time ? parseFloat(msg.response_time).toFixed(2) : '0';
                                    statsDiv.innerHTML = `
                                        <span>Time: ${elapsedTime}s</span>
                                        <span>In: ${msg.input_tokens || 0}</span>
                                        <span>Out: ${msg.output_tokens || 0}</span>
                                    `;
                                    messageDiv.parentNode.insertBefore(statsDiv, messageDiv.nextSibling);
                                }
                            });
                            // 更新当前会话ID
                            sessionKey = sKey;
                            // 关闭设置面板
                            closePanel();

                        }
                    } catch (error) {
                        console.error('Failed to fetch session messages:', error);
                    }
                    // window.location.reload();
                });
            });
        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
    }

    function formatTimestamp(value) {
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) {
            return value;
        }
        // 使用北京时间（UTC+8）格式化
        return new Date(date.getTime() + 8 * 60 * 60 * 1000).toLocaleString('zh-CN', {
            hour12: false,
            // year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    function getStoredToken() {
        const keys = ['access_token', 'token'];
        for (const key of keys) {
            const token = localStorage.getItem(key);
            if (token) {
                return { key, token };
            }
        }
        return null;
    }

    function clearStoredToken() {
        ['access_token', 'token'].forEach((key) => localStorage.removeItem(key));
        currentTokenInfo = null;
    }

    function setLoggedOutState(showReminder = false) {
        if (userInfoContainer) userInfoContainer.hidden = true;
        if (loginWrapper) loginWrapper.hidden = false;
        if (loginReminder) {
            loginReminder.hidden = !showReminder;
            if (showReminder) {
                loginReminder.textContent = "💡 Not at my smartest yet.Sign in to unlock more!";
            }
        }
    }

    function setLoggedInState(user) {
        if (loginWrapper) loginWrapper.hidden = true;
        if (userInfoContainer) {
            userInfoContainer.hidden = false;
            if (userNameEl) userNameEl.textContent = user?.username || '';
            const avatarEl = document.getElementById('userAvatarFallback');
            if (avatarEl) {
                const fallback = user?.username ? user.username[0].toUpperCase() : '';
                avatarEl.textContent = fallback;
            }
        }
        if (loginReminder) loginReminder.hidden = true;
    }

    async function checkAuthStatus() {
        // 先从 localStorage 更新 token info（如果有）
        updateTokenInfo();

        // 以 getStoredToken 为准获取 token（确保拿到最新的）
        const tokenInfo = getStoredToken();
        if (!tokenInfo) {
            // 没有 token，显示未登录状态
            setLoggedOutState(true);
            return;
        }

        // 保存并使用 tokenInfo 进行验证请求
        currentTokenInfo = tokenInfo;

        try {
            const res = await fetch(USER_INFO, {
                headers: {
                    'Accept': 'application/json',
                    'Authorization': `Bearer ${currentTokenInfo.token} `,
                },
            });

            if (!res.ok) {
                throw new Error(res.status.toString());
            }

            const userData = await res.json();
            if (userData) {
                setLoggedInState(userData);
                loadChatSessions(); // 加载会话列表
            }
            // setLoggedInState(userData);
        } catch (error) {
            console.warn('用户验证失败:', error);
            clearStoredToken();
            setLoggedOutState(true);
        }
    }

    logoutButton?.addEventListener('click', () => {
        clearStoredToken();
        setLoggedOutState(true);
    });

    // ========== 事件监听 ==========

    // 处理移动设备上的键盘弹出
    window.addEventListener('resize', () => {
        if (document.activeElement === messageInput) {
            setTimeout(() => {
                messageInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 300);
        }
    });

    messageInput.focus();
    checkAuthStatus();
    // 点击发送按钮
    sendButton.addEventListener('click', sendMessage);

    // 按Enter键发送
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 菜单选项图标反转
    sessionMenuHeader?.addEventListener('click', async () => {
        // 切换 active 类来控制显示/隐藏
        sessionMenu.classList.toggle('active');
        // 切换图标方向
        const arrow = sessionMenuHeader.querySelector('.menu-arrow');
        if (arrow) {
            arrow.classList.toggle('rotate-90');
        }
        // 如果打开 Chat sessions 菜单，加载会话数据
        if (sessionMenu.classList.contains('active')) {
            setMenuIconState(sessionMenuHeader, true);
            try {
                await loadChatSessions();
            } finally {
                setMenuIconState(sessionMenuHeader, false);
            }
        }
    });

    personaMenuHeader?.addEventListener('click', async () => {
        // 切换 active 类来控制显示/隐藏
        personaMenu.classList.toggle('active');
        // 切换图标方向
        const arrow = personaMenuHeader.querySelector('.menu-arrow');
        if (arrow) {
            arrow.classList.toggle('rotate-90');
        }
        // 如果打开 Persona 菜单，加载 Persona 数据
        if (personaMenu.classList.contains('active')) {
            setMenuIconState(personaMenuHeader, true);
            try {
                await loadPersonaSettings();
            } finally {
                setMenuIconState(personaMenuHeader, false);
            }
        }
    });

    filesMenuHeader?.addEventListener('click', async () => {
        // 切换 active 类来控制显示/隐藏
        filesMenu.classList.toggle('active');
        // 切换图标方向
        const arrow = filesMenuHeader.querySelector('.menu-arrow');
        if (arrow) {
            arrow.classList.toggle('rotate-90');
        }
        // 如果打开 Uploaded files 菜单，加载文件数据
        if (filesMenu.classList.contains('active')) {
            setMenuIconState(filesMenuHeader, true);
            try {
                await loadFilesSettings();
            } finally {
                setMenuIconState(filesMenuHeader, false);
            }
        }
    });

    // --- 侧边栏与主题切换逻辑 ---

    // 打开侧边栏
    menuIcon.addEventListener('click', () => {
        settingsPanel.classList.add('open');
        overlay.classList.add('show');
    });

    // ========== Persona 管理功能 ==========
    async function loadPersonaSettings() {
        if (!currentTokenInfo) return;

        try {
            // 测试用延迟 - 2秒钟
            // await new Promise(resolve => setTimeout(resolve, 2000));

            // 获取用户的所有 persona
            const response = await fetch('user/persona', {
                headers: {
                    'Accept': 'application/json',
                    'Authorization': `Bearer ${currentTokenInfo.token}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load personas');
            }

            const personas = await response.json();

            // 渲染 Persona 列表界面
            renderPersonaList(personas);
        } catch (error) {
            console.error('Failed to load persona settings:', error);
            personaMenu.innerHTML = '<div class="persona-message">Failed to load personas</div>';
        }
    }

    function renderPersonaList(personas) {
        personaMenu.innerHTML = `
            <div class="persona-list">
                <div class="new-persona-item persona-item">
                    <div class="persona-preview new-persona-preview">➕ New persona</div>
                </div>
                <div class="persona-items">
                    ${personas.map(persona => `
                        <div class="persona-item" data-persona-id="${persona.id}">
                            <div class="persona-name">${persona.name}</div>
                            <div class="persona-preview">${persona.profile.identity.nickname || 'No nickname'}</div>
                            <div class="default-persona-indicator">
                                ${persona.is_default ? '⭐' : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        // 添加新增 Persona 按钮事件
        const newPersonaBtn = document.querySelector('.new-persona-item');
        newPersonaBtn.addEventListener('click', async () => {
            await showPersonaModal();
        });

        // 添加 Persona 项点击事件（进入编辑）
        document.querySelectorAll('.persona-item:not(.new-persona-item)').forEach(item => {
            item.addEventListener('click', async () => {
                const personaId = item.getAttribute('data-persona-id');
                const persona = personas.find(p => p.id === personaId);
                if (persona) {
                    await showPersonaModal(persona);
                }
            });
        });
    }

    async function showPersonaModal(persona = null) {
        const isEdit = persona !== null;
        const profile = persona?.profile || {};
        const identity = profile.identity || {};
        const learning = profile.learning || {};
        const motivation = profile.motivation || {};
        const routines = profile.routines || {};
        const communication = profile.communication || {};
        const assessment = profile.assessment || {};
        const safety = profile.safety || {};
        const meta = profile.meta || {};

        // 获取用户的所有persona来检查是否可以设置默认
        let personas = [];
        let canSetDefault = true;
        try {
            const response = await fetch('user/persona', {
                headers: {
                    'Accept': 'application/json',
                    'Authorization': `Bearer ${currentTokenInfo.token}`
                }
            });
            if (response.ok) {
                personas = await response.json();
                // 如果只有一个persona且正在编辑该persona，则不可设置默认
                if (personas.length === 1 && isEdit && personas[0].id === persona.id) {
                    canSetDefault = false;
                }
            }
        } catch (error) {
            console.error('Failed to load personas for default check:', error);
        }

        const modalHtml = `
            <div id="persona-modal" class="persona-modal">
                <div class="persona-modal-content">
                    <div class="persona-modal-header">
                        <div class="default-persona-checkbox">
                            <div class="checkbox-group">
                                <div class="checkbox-item">
                                    <input type="checkbox" id="defaultPersona" name="defaultPersona" ${persona?.is_default ? 'checked' : ''} ${!canSetDefault ? 'disabled' : ''}>
                                    <label for="defaultPersona">Default persona</label>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="persona-modal-body">
                        <div class="persona-name-input">
                            <input type="text" id="personaName" name="personaName" value="${persona?.name || ''}" placeholder="Persona name" required>
                        </div>
                        <form id="personaForm">
                            <!-- Identity Section -->
                            <div class="config-section">
                                <h4>Identity</h4>
                                <div class="form-group">
                                    <label for="nickname">Nickname:</label>
                                    <input type="text" id="nickname" name="nickname" value="${identity.nickname || ''}" placeholder="ie. Michael Xiong">
                                </div>
                                <div class="form-group">
                                    <label for="birth_month">Birth Month:</label>
                                    <input type="text" id="birth_month" name="birth_month" value="${identity.birth_month || ''}" placeholder="ie. 2018-12">
                                </div>
                                <div class="form-group">
                                    <label for="grade_level">Grade Level:</label>
                                    <input type="text" id="grade_level" name="grade_level" value="${identity.grade_level || ''}" placeholder="ie. Grade 10">
                                </div>
                                <div class="form-group">
                                    <label for="locale">Locale:</label>
                                    <input type="text" id="locale" name="locale" value="${identity.locale || 'CN'}" placeholder="ie. CN">
                                </div>
                                <div class="form-group">
                                    <label for="timezone">Timezone:</label>
                                    <input type="text" id="timezone" name="timezone" value="${identity.timezone || 'Asia/Shanghai'}" placeholder="ie. Asia/Shanghai">
                                </div>
                                <div class="form-group">
                                    <label for="primary_language">Primary Language:</label>
                                    <input type="text" id="primary_language" name="primary_language" value="${identity.primary_language || 'zh-CN'}" placeholder="ie. zh-CN">
                                </div>
                                <div class="form-group switch-group">
                                    <label class="switch-label">Bilingual:</label>
                                    <div class="switch-container">
                                        <label class="switch">
                                            <input type="checkbox" id="bilingual" name="bilingual" ${identity.bilingual ? 'checked' : ''}>
                                            <span class="slider round"></span>
                                        </label>
                                        <span class="switch-status">${identity.bilingual ? 'Yes' : 'No'}</span>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label for="CEFR_level">CEFR Level:</label>
                                    <input type="text" id="CEFR_level" name="CEFR_level" value="${identity.CEFR_level || 'A2'}" placeholder="ie. A2">
                                </div>
                            </div>

                            <!-- Learning Section -->
                            <div class="config-section">
                                <h4>Learning Preferences</h4>
                                <div class="form-group">
                                    <label for="strengths">Strengths:</label>
                                    <input type="text" id="strengths" name="strengths" value="${learning.strengths ? learning.strengths.join(', ') : ''}" placeholder="ie. Math, Science">
                                </div>
                                <div class="form-group">
                                    <label for="challenges">Challenges:</label>
                                    <input type="text" id="challenges" name="challenges" value="${learning.challenges ? learning.challenges.join(', ') : ''}" placeholder="ie. Writing, History">
                                </div>
                                <div class="form-group">
                                    <label for="short_term_goal">Short Term Goal:</label>
                                    <input type="text" id="short_term_goal" name="short_term_goal" value="${learning.goals?.short_term || ''}" placeholder="ie. Improve math skills">
                                </div>
                                <div class="form-group">
                                    <label for="long_term_goal">Long Term Goal:</label>
                                    <input type="text" id="long_term_goal" name="long_term_goal" value="${learning.goals?.long_term || ''}" placeholder="ie. Get into top university">
                                </div>
                                <div class="form-group">
                                    <label for="subjects_focus">Subjects Focus:</label>
                                    <input type="text" id="subjects_focus" name="subjects_focus" value="${learning.subjects_focus ? learning.subjects_focus.join(', ') : ''}" placeholder="ie. Math, Physics, Chemistry">
                                </div>
                                <div class="form-group">
                                    <label for="preferred_modalities">Preferred Modalities:</label>
                                    <div class="checkbox-group" id="preferred_modalities_container">
                                        <div class="checkbox-item">
                                            <input type="checkbox" id="modality_visual" name="preferred_modalities" value="visual" ${learning.preferred_modalities?.includes('visual') ? 'checked' : ''}>
                                            <label for="modality_visual">Visual</label>
                                        </div>
                                        <div class="checkbox-item">
                                            <input type="checkbox" id="modality_auditory" name="preferred_modalities" value="auditory" ${learning.preferred_modalities?.includes('auditory') ? 'checked' : ''}>
                                            <label for="modality_auditory">Auditory</label>
                                        </div>
                                        <div class="checkbox-item">
                                            <input type="checkbox" id="modality_kinesthetic" name="preferred_modalities" value="kinesthetic" ${learning.preferred_modalities?.includes('kinesthetic') ? 'checked' : ''}>
                                            <label for="modality_kinesthetic">Kinesthetic</label>
                                        </div>
                                        <div class="checkbox-item">
                                            <input type="checkbox" id="modality_reading" name="preferred_modalities" value="reading" ${learning.preferred_modalities?.includes('reading') ? 'checked' : ''}>
                                            <label for="modality_reading">Reading</label>
                                        </div>
                                        <div class="checkbox-item">
                                            <input type="checkbox" id="modality_interactive" name="preferred_modalities" value="interactive" ${learning.preferred_modalities?.includes('interactive') ? 'checked' : ''}>
                                            <label for="modality_interactive">Interactive</label>
                                        </div>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label>Learning Pace:</label>
                                    <div class="radio-group">
                                        <label class="radio-item">
                                            <input type="radio" id="pace_slow" name="pace" value="slow" ${learning.pace === 'slow' ? 'checked' : ''}>
                                            <label for="pace_slow">Slow</label>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" id="pace_normal" name="pace" value="normal" ${learning.pace === 'normal' || !learning.pace ? 'checked' : ''}>
                                            <label for="pace_normal">Normal</label>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" id="pace_fast" name="pace" value="fast" ${learning.pace === 'fast' ? 'checked' : ''}>
                                            <label for="pace_fast">Fast</label>
                                        </label>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label>Scaffolding Level:</label>
                                    <div class="radio-group">
                                        <label class="radio-item">
                                            <input type="radio" name="scaffolding_level" value="low" ${learning.scaffolding_level === 'low' ? 'checked' : ''}>
                                            <span>Low</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="scaffolding_level" value="medium" ${learning.scaffolding_level === 'medium' || !learning.scaffolding_level ? 'checked' : ''}>
                                            <span>Medium</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="scaffolding_level" value="high" ${learning.scaffolding_level === 'high' ? 'checked' : ''}>
                                            <span>High</span>
                                        </label>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label>Examples Preference:</label>
                                    <div class="radio-group">
                                        <label class="radio-item">
                                            <input type="radio" name="examples_preference" value="real_life" ${learning.examples_preference === 'real_life' || !learning.examples_preference ? 'checked' : ''}>
                                            <span>Real Life</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="examples_preference" value="abstract" ${learning.examples_preference === 'abstract' ? 'checked' : ''}>
                                            <span>Abstract</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="examples_preference" value="academic" ${learning.examples_preference === 'academic' ? 'checked' : ''}>
                                            <span>Academic</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="examples_preference" value="interactive" ${learning.examples_preference === 'interactive' ? 'checked' : ''}>
                                            <span>Interactive</span>
                                        </label>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label>Error Correction Style:</label>
                                    <div class="radio-group">
                                        <label class="radio-item">
                                            <input type="radio" name="error_correction_style" value="socratic" ${learning.error_correction_style === 'socratic' || !learning.error_correction_style ? 'checked' : ''}>
                                            <span>Socratic</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="error_correction_style" value="direct" ${learning.error_correction_style === 'direct' ? 'checked' : ''}>
                                            <span>Direct</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="error_correction_style" value="gentle" ${learning.error_correction_style === 'gentle' ? 'checked' : ''}>
                                            <span>Gentle</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="error_correction_style" value="step_by_step" ${learning.error_correction_style === 'step_by_step' ? 'checked' : ''}>
                                            <span>Step by Step</span>
                                        </label>
                                    </div>
                                </div>
                            </div>

                            <!-- Motivation Section -->
                            <div class="config-section">
                                <h4>Motivation & Engagement</h4>
                                <div class="form-group">
                                    <label>Tone:</label>
                                    <div class="radio-group">
                                        <label class="radio-item">
                                            <input type="radio" name="tone" value="encouraging" ${motivation.tone === 'encouraging' || !motivation.tone ? 'checked' : ''}>
                                            <span>Encouraging</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="tone" value="friendly" ${motivation.tone === 'friendly' ? 'checked' : ''}>
                                            <span>Friendly</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="tone" value="professional" ${motivation.tone === 'professional' ? 'checked' : ''}>
                                            <span>Professional</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="tone" value="strict" ${motivation.tone === 'strict' ? 'checked' : ''}>
                                            <span>Strict</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="tone" value="humorous" ${motivation.tone === 'humorous' ? 'checked' : ''}>
                                            <span>Humorous</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="tone" value="calm" ${motivation.tone === 'calm' ? 'checked' : ''}>
                                            <span>Calm</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="tone" value="casual" ${motivation.tone === 'casual' ? 'checked' : ''}>
                                            <span>Casual</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="tone" value="enthusiastic" ${motivation.tone === 'enthusiastic' ? 'checked' : ''}>
                                            <span>Enthusiastic</span>
                                        </label>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label>Praise Frequency:</label>
                                    <div class="radio-group">
                                        <label class="radio-item">
                                            <input type="radio" name="praise_frequency" value="low" ${motivation.praise_frequency === 'low' ? 'checked' : ''}>
                                            <span>Low</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="praise_frequency" value="moderate" ${motivation.praise_frequency === 'moderate' || !motivation.praise_frequency ? 'checked' : ''}>
                                            <span>Moderate</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="praise_frequency" value="high" ${motivation.praise_frequency === 'high' ? 'checked' : ''}>
                                            <span>High</span>
                                        </label>
                                    </div>
                                </div>
                                <div class="form-group switch-group">
                                    <label class="switch-label">Gamification:</label>
                                    <div class="switch-container">
                                        <label class="switch">
                                            <input type="checkbox" id="gamification" name="gamification" ${motivation.gamification ? 'checked' : ''}>
                                            <span class="slider round"></span>
                                        </label>
                                        <span class="switch-status">${motivation.gamification ? 'Yes' : 'No'}</span>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label for="interests">Interests:</label>
                                    <input type="text" id="interests" name="interests" value="${motivation.interests ? motivation.interests.join(', ') : ''}" placeholder="ie. Sports, Music, Art">
                                </div>
                                <div class="form-group switch-group">
                                    <label class="switch-label">Emotion Check-in:</label>
                                    <div class="switch-container">
                                        <label class="switch">
                                            <input type="checkbox" id="emotion_checkin" name="emotion_checkin" ${motivation.emotion_checkin !== false ? 'checked' : ''}>
                                            <span class="slider round"></span>
                                        </label>
                                        <span class="switch-status">${motivation.emotion_checkin !== false ? 'Yes' : 'No'}</span>
                                    </div>
                                </div>
                                <div class="form-group switch-group">
                                    <label class="switch-label">Growth Mindset:</label>
                                    <div class="switch-container">
                                        <label class="switch">
                                            <input type="checkbox" id="growth_mindset" name="growth_mindset" ${motivation.growth_mindset !== false ? 'checked' : ''}>
                                            <span class="slider round"></span>
                                        </label>
                                        <span class="switch-status">${motivation.growth_mindset !== false ? 'Yes' : 'No'}</span>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label for="reward_scheme">Reward Scheme:</label>
                                    <input type="text" id="reward_scheme" name="reward_scheme" value="${motivation.reward_scheme || ''}" placeholder="ie. Complete 3 questions to get 1 badge">
                                </div>
                            </div>

                            <!-- Routines Section -->
                            <div class="config-section">
                                <h4>Study Routines</h4>
                                <div class="form-group">
                                    <label for="session_length_max">Max Session Length (minutes):</label>
                                    <input type="number" id="session_length_max" name="session_length_max" value="${routines.session_length_max || 60}" min="5" max="180">
                                </div>
                                <div class="form-group">
                                    <label for="break_interval_min">Break Interval (minutes):</label>
                                    <input type="number" id="break_interval_min" name="break_interval_min" value="${routines.break_interval_min || 15}" min="5" max="45">
                                </div>
                                <div class="form-group">
                                    <label for="homework_policy">Homework Policy:</label>
                                    <input id="homework_policy" name="homework_policy" placeholder="ie. Don't give direct answers, provide hints and key concepts" value="${routines.homework_policy || ''}">
                                </div>
                                <div class="form-group switch-group">
                                    <label class="switch-label">Offline Suggestions:</label>
                                    <div class="switch-container">
                                        <label class="switch">
                                            <input type="checkbox" id="offline_suggestions" name="offline_suggestions" ${routines.offline_suggestions !== false ? 'checked' : ''}>
                                            <span class="slider round"></span>
                                        </label>
                                        <span class="switch-status">${routines.offline_suggestions !== false ? 'Yes' : 'No'}</span>
                                    </div>
                                </div>
                            </div>

                            <!-- Communication Section -->
                            <div class="config-section">
                                <h4>Communication Style</h4>
                                <div class="form-group switch-group">
                                    <label class="switch-label">Use Emoji:</label>
                                    <div class="switch-container">
                                        <label class="switch">
                                            <input type="checkbox" id="emoji" name="emoji" ${communication.emoji !== false ? 'checked' : ''}>
                                            <span class="slider round"></span>
                                        </label>
                                        <span class="switch-status">${communication.emoji !== false ? 'Yes' : 'No'}</span>
                                    </div>
                                </div>
                                <div class="form-group switch-group">
                                    <label class="switch-label">Step by Step Explanation:</label>
                                    <div class="switch-container">
                                        <label class="switch">
                                            <input type="checkbox" id="step_by_step" name="step_by_step" ${communication.step_by_step !== false ? 'checked' : ''}>
                                            <span class="slider round"></span>
                                        </label>
                                        <span class="switch-status">${communication.step_by_step !== false ? 'Yes' : 'No'}</span>
                                    </div>
                                </div>
                                <div class="form-group switch-group">
                                    <label class="switch-label">Ask Before Answer:</label>
                                    <div class="switch-container">
                                        <label class="switch">
                                            <input type="checkbox" id="ask_before_answer" name="ask_before_answer" ${communication.ask_before_answer !== false ? 'checked' : ''}>
                                            <span class="slider round"></span>
                                        </label>
                                        <span class="switch-status">${communication.ask_before_answer !== false ? 'Yes' : 'No'}</span>
                                    </div>
                                </div>
                            </div>

                            <!-- Assessment Section -->
                            <div class="config-section">
                                <h4>Assessment & Progress</h4>
                                <div class="form-group">
                                    <label>Quiz Style:</label>
                                    <div class="radio-group">
                                        <label class="radio-item">
                                            <input type="radio" name="quiz_style" value="multiple_choice" ${assessment.quiz_style === 'multiple_choice' || !assessment.quiz_style ? 'checked' : ''}>
                                            <span>Multiple Choice</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="quiz_style" value="true_false" ${assessment.quiz_style === 'true_false' ? 'checked' : ''}>
                                            <span>True/False</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="quiz_style" value="fill_in_the_blank" ${assessment.quiz_style === 'fill_in_the_blank' ? 'checked' : ''}>
                                            <span>Fill in the Blank</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="quiz_style" value="short_answer" ${assessment.quiz_style === 'short_answer' ? 'checked' : ''}>
                                            <span>Short Answer</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="quiz_style" value="essay" ${assessment.quiz_style === 'essay' ? 'checked' : ''}>
                                            <span>Essay</span>
                                        </label>
                                    </div>
                                </div>
                                <div class="form-group switch-group">
                                    <label class="switch-label">Adapt Difficulty:</label>
                                    <div class="switch-container">
                                        <label class="switch">
                                            <input type="checkbox" id="adapt_difficulty" name="adapt_difficulty" ${assessment.adapt_difficulty !== false ? 'checked' : ''}>
                                            <span class="slider round"></span>
                                        </label>
                                        <span class="switch-status">${assessment.adapt_difficulty !== false ? 'Yes' : 'No'}</span>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label for="mastery_threshold">Mastery Threshold (0.5-1.0):</label>
                                    <input type="number" id="mastery_threshold" name="mastery_threshold" value="${assessment.mastery_threshold || 0.8}" min="0.5" max="1.0" step="0.1">
                                </div>
                                <div class="form-group switch-group">
                                    <label class="switch-label">Spaced Repetition:</label>
                                    <div class="switch-container">
                                        <label class="switch">
                                            <input type="checkbox" id="spaced_repetition" name="spaced_repetition" ${assessment.spaced_repetition !== false ? 'checked' : ''}>
                                            <span class="slider round"></span>
                                        </label>
                                        <span class="switch-status">${assessment.spaced_repetition !== false ? 'Yes' : 'No'}</span>
                                    </div>
                                </div>
                            </div>

                            <!-- Safety Section -->
                            <div class="config-section">
                                <h4>Safety & Content</h4>
                                <div class="form-group switch-group">
                                    <label for="external_links_allowed">External Links Allowed:</label>
                                    <div class="switch-container">
                                        <label class="switch">
                                            <input type="checkbox" id="external_links_allowed" name="external_links_allowed" ${safety.external_links_allowed !== false ? 'checked' : ''}>
                                            <span class="slider round"></span>
                                        </label>
                                        <span class="switch-status">${safety.external_links_allowed !== false ? 'Yes' : 'No'}</span>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label>Content Level:</label>
                                    <div class="radio-group">
                                        <label class="radio-item">
                                            <input type="radio" name="content_level" value="k12-safe" ${safety.content_level === 'k12-safe' || !safety.content_level ? 'checked' : ''}>
                                            <span>K12 Safe</span>
                                        </label>
                                        <label class="radio-item">
                                            <input type="radio" name="content_level" value="general-safe" ${safety.content_level === 'general-safe' ? 'checked' : ''}>
                                            <span>General Safe</span>
                                        </label>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label>Prohibited Topics:</label>
                                    <div class="checkbox-group">
                                        <div class="checkbox-item">
                                            <input type="checkbox" id="prohibited_violent" name="prohibited_topics" value="Violent" ${safety.prohibited_topics?.includes('Violent') ? 'checked' : ''}>
                                            <label for="prohibited_violent">Violent</label>
                                        </div>
                                        <div class="checkbox-item">
                                            <input type="checkbox" id="prohibited_adult" name="prohibited_topics" value="Adult" ${safety.prohibited_topics?.includes('Adult') ? 'checked' : ''}>
                                            <label for="prohibited_adult">Adult</label>
                                        </div>
                                        <div class="checkbox-item">
                                            <input type="checkbox" id="prohibited_drugs" name="prohibited_topics" value="Drugs" ${safety.prohibited_topics?.includes('Drugs') ? 'checked' : ''}>
                                            <label for="prohibited_drugs">Drugs</label>
                                        </div>
                                        <div class="checkbox-item">
                                            <input type="checkbox" id="prohibited_weapons" name="prohibited_topics" value="Weapons" ${safety.prohibited_topics?.includes('Weapons') ? 'checked' : ''}>
                                            <label for="prohibited_weapons">Weapons</label>
                                        </div>
                                        <div class="checkbox-item">
                                            <input type="checkbox" id="prohibited_politics" name="prohibited_topics" value="Politics" ${safety.prohibited_topics?.includes('Politics') ? 'checked' : ''}>
                                            <label for="prohibited_politics">Politics</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Meta Section -->
                            <div class="config-section">
                                <h4>Meta Information</h4>
                                <div class="form-group">
                                    <label for="notes">Notes:</label>
                                    <input id="notes" name="notes" placeholder="Additional notes about this persona">${meta.notes || ''}</input>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="persona-modal-footer">
                        <button id="save-persona" class="save-btn">Save</button>
                    </div>
                </div>
            </div>
        `;

        // 移除现有模态框
        const existingModal = document.getElementById('persona-modal');
        if (existingModal) {
            existingModal.remove();
        }

        // 添加新模态框
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modal = document.getElementById('persona-modal');

        // 添加事件监听
        document.getElementById('save-persona').addEventListener('click', () => {
            savePersona(persona?.id);
        });

        // 开关按钮标签更新
        const switchElements = document.querySelectorAll('.switch-group');
        switchElements.forEach(group => {
            const switchInput = group.querySelector('input[type="checkbox"]');
            const statusLabel = group.querySelector('.switch-status');
            if (switchInput && statusLabel) {
                // 初始化状态
                statusLabel.textContent = switchInput.checked ? 'Yes' : 'No';

                // 添加事件监听
                switchInput.addEventListener('change', () => {
                    statusLabel.textContent = switchInput.checked ? 'Yes' : 'No';
                });
            }
        });

        // Default persona勾选框事件监听
        const defaultPersonaCheckbox = document.getElementById('defaultPersona');
        if (defaultPersonaCheckbox) {
            // 如果已经是默认persona，则阻止取消勾选
            if (persona?.is_default) {
                // 阻止取消勾选
                defaultPersonaCheckbox.addEventListener('click', (e) => {
                    if (defaultPersonaCheckbox.checked) {
                        e.preventDefault();
                        return false;
                    }
                });

                // 阻止通过键盘取消勾选
                defaultPersonaCheckbox.addEventListener('keydown', (e) => {
                    if (defaultPersonaCheckbox.checked && (e.key === ' ' || e.key === 'Enter')) {
                        e.preventDefault();
                        return false;
                    }
                });
            }

            // 添加事件监听 - 勾选时立即保存
            defaultPersonaCheckbox.addEventListener('change', async () => {
                // 如果正在编辑persona且勾选了，立即保存默认状态
                if (persona && defaultPersonaCheckbox.checked && !defaultPersonaCheckbox.disabled) {
                    await saveDefaultPersona(persona.id, true);

                    // 勾选后阻止取消勾选（但不禁用勾选框，因为其他persona可以勾选）
                    defaultPersonaCheckbox.addEventListener('click', (e) => {
                        if (defaultPersonaCheckbox.checked) {
                            e.preventDefault();
                            return false;
                        }
                    });

                    defaultPersonaCheckbox.addEventListener('keydown', (e) => {
                        if (defaultPersonaCheckbox.checked && (e.key === ' ' || e.key === 'Enter')) {
                            e.preventDefault();
                            return false;
                        }
                    });
                }
            });
        }

        // 点击模态框外部关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

        // 阻止模态框内容点击事件冒泡
        const modalContent = document.querySelector('.persona-modal-content');
        modalContent.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    async function savePersona(personaId = null) {
        if (!currentTokenInfo) {
            personaShowError('请先登录');
            return;
        }

        const form = document.getElementById('personaForm');
        const formData = new FormData(form);

        // 获取所有表单数据
        const personaName = document.getElementById('personaName').value;
        const isDefaultPersona = document.getElementById('defaultPersona')?.checked || false;
        const nickname = formData.get('nickname');
        const birth_month = formData.get('birth_month');
        const grade_level = formData.get('grade_level');
        const locale = formData.get('locale');
        const timezone = formData.get('timezone');
        const primary_language = formData.get('primary_language');
        const bilingual = formData.get('bilingual') === 'on';
        const CEFR_level = formData.get('CEFR_level');

        // Learning fields
        const strengths = formData.get('strengths') ? formData.get('strengths').split(',').map(s => s.trim()).filter(s => s) : [];
        const challenges = formData.get('challenges') ? formData.get('challenges').split(',').map(s => s.trim()).filter(s => s) : [];
        const short_term_goal = formData.get('short_term_goal');
        const long_term_goal = formData.get('long_term_goal');
        const subjects_focus = formData.get('subjects_focus') ? formData.get('subjects_focus').split(',').map(s => s.trim()).filter(s => s) : [];
        const preferred_modalities = Array.from(document.querySelectorAll('input[name="preferred_modalities"]:checked')).map(checkbox => checkbox.value);
        const pace = formData.get('pace');
        const scaffolding_level = formData.get('scaffolding_level');
        const examples_preference = formData.get('examples_preference');
        const error_correction_style = formData.get('error_correction_style');

        // Motivation fields
        const tone = formData.get('tone');
        const praise_frequency = formData.get('praise_frequency');
        const gamification = formData.get('gamification') === 'on';
        const interests = formData.get('interests') ? formData.get('interests').split(',').map(s => s.trim()).filter(s => s) : [];
        const emotion_checkin = formData.get('emotion_checkin') === 'on';
        const growth_mindset = formData.get('growth_mindset') === 'on';
        const reward_scheme = formData.get('reward_scheme');

        // Routines fields
        const session_length_max = parseInt(formData.get('session_length_max')) || 60;
        const break_interval_min = parseInt(formData.get('break_interval_min')) || 15;
        const homework_policy = formData.get('homework_policy');
        const offline_suggestions = formData.get('offline_suggestions') === 'on';

        // Communication fields
        const emoji = formData.get('emoji') === 'on';
        const step_by_step = formData.get('step_by_step') === 'on';
        const ask_before_answer = formData.get('ask_before_answer') === 'on';

        // Assessment fields
        const quiz_style = formData.get('quiz_style');
        const adapt_difficulty = formData.get('adapt_difficulty') === 'on';
        const mastery_threshold = parseFloat(formData.get('mastery_threshold')) || 0.8;
        const spaced_repetition = formData.get('spaced_repetition') === 'on';

        // Safety fields
        const external_links_allowed = formData.get('external_links_allowed') === 'on';
        const content_level = formData.get('content_level');
        const prohibited_topics = Array.from(document.querySelectorAll('input[name="prohibited_topics"]:checked')).map(checkbox => checkbox.value);

        // Meta fields
        const notes = formData.get('notes');

        if (!personaName) {
            personaShowError('Persona name must be required！');
            return;
        }

        // 检查persona名称是否重复
        try {
            const personasResponse = await fetch('user/persona', {
                headers: {
                    'Accept': 'application/json',
                    'Authorization': `Bearer ${currentTokenInfo.token}`
                }
            });

            if (personasResponse.ok) {
                const existingPersonas = await personasResponse.json();
                // console.log('Existing personas:', existingPersonas);
                // console.log('Checking name:', personaName, 'for personaId:', personaId);

                // 检查是否有相同名称的persona（排除当前编辑的persona）
                const duplicatePersona = existingPersonas.find(p =>
                    p.name === personaName && (!personaId || p.id !== personaId)
                );

                // console.log('Duplicate persona found:', duplicatePersona);

                if (duplicatePersona) {
                    personaShowError('Persona name already exists!');
                    return;
                }
            } else {
                console.error('Failed to fetch personas for name check:', personasResponse.status);
            }
        } catch (error) {
            console.error('Failed to check persona name uniqueness:', error);
            // 继续保存，让后端进行最终验证
        }

        try {
            const profileData = {
                identity: {
                    nickname: nickname,
                    birth_month: birth_month,
                    grade_level: grade_level,
                    locale: locale,
                    timezone: timezone,
                    primary_language: primary_language,
                    bilingual: bilingual,
                    CEFR_level: CEFR_level
                },
                learning: {
                    strengths: strengths,
                    challenges: challenges,
                    goals: {
                        short_term: short_term_goal,
                        long_term: long_term_goal
                    },
                    subjects_focus: subjects_focus,
                    preferred_modalities: preferred_modalities,
                    pace: pace,
                    scaffolding_level: scaffolding_level,
                    examples_preference: examples_preference,
                    error_correction_style: error_correction_style
                },
                motivation: {
                    tone: tone,
                    praise_frequency: praise_frequency,
                    gamification: gamification,
                    interests: interests,
                    emotion_checkin: emotion_checkin,
                    growth_mindset: growth_mindset,
                    reward_scheme: reward_scheme
                },
                routines: {
                    session_length_max: session_length_max,
                    break_interval_min: break_interval_min,
                    homework_policy: homework_policy,
                    offline_suggestions: offline_suggestions
                },
                communication: {
                    emoji: emoji,
                    step_by_step: step_by_step,
                    ask_before_answer: ask_before_answer
                },
                assessment: {
                    quiz_style: quiz_style,
                    adapt_difficulty: adapt_difficulty,
                    mastery_threshold: mastery_threshold,
                    spaced_repetition: spaced_repetition
                },
                safety: {
                    external_links_allowed: external_links_allowed,
                    content_level: content_level,
                    prohibited_topics: prohibited_topics
                },
                meta: {
                    notes: notes
                }
            };

            let response;
            if (personaId) {
                // 更新现有 Persona
                response = await fetch(`user/persona/${personaId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${currentTokenInfo.token}`
                    },
                    body: JSON.stringify({
                        name: personaName,
                        profile: profileData,
                        is_default: isDefaultPersona
                    })
                });
            } else {
                // 创建新 Persona
                response = await fetch('user/persona', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${currentTokenInfo.token}`
                    },
                    body: JSON.stringify({
                        name: personaName,
                        profile: profileData,
                        is_default: isDefaultPersona
                    })
                });
            }

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to save persona');
            }

            // 使用persona专用成功提示
            personaShowSuccess('Update persona successfully~');

        } catch (error) {
            console.error('Failed to save persona:', error);
            personaShowError('Failed to save persona: ' + error.message);
        }
    }

    async function setDefaultPersona(personaId) {
        if (!currentTokenInfo) return;

        try {
            const response = await fetch(`user/persona/${personaId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${currentTokenInfo.token}`
                },
                body: JSON.stringify({
                    is_default: true
                })
            });

            if (!response.ok) {
                throw new Error('Failed to set default persona');
            }

            // 不再显示成功提示，静默刷新列表
            loadPersonaSettings(); // 刷新列表

        } catch (error) {
            console.error('Failed to set default persona:', error);
            showError('Failed to set default persona');
        }
    }

    // 保存默认persona状态
    async function saveDefaultPersona(personaId, isDefault) {
        if (!currentTokenInfo) return;

        try {
            const response = await fetch(`user/persona/${personaId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${currentTokenInfo.token}`
                },
                body: JSON.stringify({
                    is_default: isDefault
                })
            });

            // 初始化移动端键盘处理
            setupMobileKeyboardHandling();

            if (!response.ok) {
                throw new Error('Failed to update default persona');
            }

            // 立即刷新列表
            loadPersonaSettings();

        } catch (error) {
            console.error('Failed to update default persona:', error);
            // 恢复勾选框状态
            const defaultPersonaCheckbox = document.getElementById('defaultPersona');
            if (defaultPersonaCheckbox) {
                defaultPersonaCheckbox.checked = false;
            }
            showError('Failed to update default persona');
        }
    }

    // 关闭侧边栏
    function closePanel() {
        settingsPanel.classList.remove('open');
        overlay.classList.remove('show');

    }

    closeSettingsBtn.addEventListener('click', closePanel);
    overlay.addEventListener('click', closePanel);

    // 检查并应用已保存的主题
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme === 'dark') {
        document.body.classList.add('dark-theme');
        themeToggleSwitch.checked = true; // 同步开关状态
    }

    // 监听新开关的切换事件
    themeToggleSwitch.addEventListener('change', () => {
        document.body.classList.toggle('dark-theme');
        const isDark = document.body.classList.contains('dark-theme');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });

    // ========== Uploaded Files 管理功能 ==========
    async function loadFilesSettings() {
        if (!currentTokenInfo) return;

        try {
            // 获取用户的个人文件
            const response = await fetch('/file/list?include_personal=true', {
                headers: {
                    'Accept': 'application/json',
                    'Authorization': `Bearer ${currentTokenInfo.token}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load files');
            }

            const files = await response.json();

            // 渲染文件列表界面
            renderFilesList(files);
        } catch (error) {
            console.error('Failed to load files:', error);
            const filesList = document.querySelector('.files-list');
            if (filesList) {
                filesList.innerHTML = '<div class="persona-message">Failed to load files</div>';
            }
        }
    }

    function renderFilesList(files) {
        const filesList = document.querySelector('.files-list');
        if (!filesList) return;

        filesList.innerHTML = `
            <div class="file-item new-file-item">
                <div class="file-name new-file-preview">➕ Upload file</div>
            </div>
            <div class="file-items">
                ${files.map(file => `
                    <div class="file-item" data-file-id="${file.id}">
                        <div class="file-name">${escapeHtml(file.file_name)}</div>
                        <div class="file-info">
                            <span class="file-size">${formatFileSize(file.file_size)}</span>
                            <span class="file-time">${formatFileTime(file.created_at)}</span>
                        </div>
                        <div class="file-actions">
                            <button class="delete-file-btn" title="Delete file">
                                <svg viewBox="0 0 24 24">
                                    <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        // 添加上传文件按钮事件
        const uploadFileBtn = document.querySelector('.new-file-item');
        uploadFileBtn.addEventListener('click', () => {
            triggerFileUpload();
        });

        // 添加文件项点击事件（预览）
        document.querySelectorAll('.file-item:not(.new-file-item)').forEach(item => {
            item.addEventListener('click', (e) => {
                // 如果点击的是删除按钮，不触发预览
                if (e.target.closest('.delete-file-btn')) {
                    return;
                }
                const fileId = item.getAttribute('data-file-id');
                const file = files.find(f => f.id === fileId);
                if (file) {
                    showFilePreview(file);
                }
            });
        });

        // 添加删除按钮事件
        document.querySelectorAll('.delete-file-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                e.preventDefault();

                const fileItem = e.target.closest('.file-item');
                const fileId = fileItem.getAttribute('data-file-id');
                const fileName = fileItem.querySelector('.file-name').textContent;
                const fileSize = fileItem.querySelector('.file-size').textContent;

                if (fileId) {
                    try {
                        const confirmed = await showConfirmDialog(
                            'Delete File',
                            'Are you sure you want to delete this file? This action cannot be undone.',
                            {
                                name: fileName,
                                size: fileSize
                            }
                        );

                        if (confirmed) {
                            await deleteFile(fileId);
                        }
                    } catch (error) {
                        console.error('Error in delete confirmation:', error);
                        showError('Failed to delete file: ' + error.message);
                    }
                } else {
                    showError('Cannot delete file: File ID not found');
                }
            });
        });
    }

    function triggerFileUpload() {
        // 创建隐藏的文件输入元素
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.className = 'file-upload-input';
        fileInput.accept = '.jpeg,.jpg,.png,.gif,.webp,.mp3,.wav,.ogg,.mp4,.webm,.pdf,.txt,.doc,.docx';

        fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (file) {
                await uploadFile(file);
            }
            // 清理输入元素
            fileInput.remove();
        });

        // 触发文件选择
        fileInput.click();
    }

    async function uploadFile(file) {
        if (!currentTokenInfo) {
            showError('Please login to upload files');
            return;
        }

        // 检查文件大小（100MB限制）
        if (file.size > 100 * 1024 * 1024) {
            showError('File size cannot exceed 100MB');
            return;
        }

        try {
            const formData = new FormData();
            formData.append('file', file);
            // 作为个人文件上传，不关联会话
            formData.append('session_id', '');

            const response = await fetch('/file/upload', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${currentTokenInfo.token}`
                },
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Upload failed');
            }

            const uploadedFile = await response.json();
            showError('File uploaded successfully');

            // 刷新文件列表
            await loadFilesSettings();

        } catch (error) {
            console.error('File upload failed:', error);
            showError('Upload failed: ' + error.message);
        }
    }

    async function deleteFile(fileId) {
        if (!currentTokenInfo) {
            showError('Please login to delete files');
            return;
        }

        try {
            const response = await fetch(`/file/${fileId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${currentTokenInfo.token}`
                }
            });

            if (!response.ok) {
                throw new Error('Delete failed');
            }

            showError('File deleted successfully');

            // 刷新文件列表
            await loadFilesSettings();

        } catch (error) {
            console.error('File delete failed:', error);
            showError('Delete failed: ' + error.message);
        }
    }

    function showFilePreview(file) {
        const modalHtml = `
            <div id="file-preview-modal" class="file-preview-modal">
                <div class="file-preview-content">
                    <div class="file-preview-header">
                        <h3 class="file-preview-title">${escapeHtml(file.file_name)}</h3>
                        <button class="close-preview-btn">&times;</button>
                    </div>
                    <div class="file-preview-body">
                        ${getFilePreviewContent(file)}
                    </div>
                    <div class="file-preview-footer">
                        <div class="file-info">
                            <span>Size: ${formatFileSize(file.file_size)}</span>
                            <span>Uploaded: ${formatFileTime(file.created_at)}</span>
                        </div>
                        <a href="${file.file_url}" class="download-file-btn" download="${file.file_name}">
                            <svg viewBox="0 0 24 24" width="16" height="16">
                                <path fill="currentColor" d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
                            </svg>
                            Download
                        </a>
                    </div>
                </div>
            </div>
        `;

        // 移除现有模态框
        const existingModal = document.getElementById('file-preview-modal');
        if (existingModal) {
            existingModal.remove();
        }

        // 添加新模态框
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modal = document.getElementById('file-preview-modal');

        // 添加事件监听
        const closeBtn = modal.querySelector('.close-preview-btn');
        closeBtn.addEventListener('click', () => {
            modal.remove();
        });

        // 点击模态框外部关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

        // 阻止模态框内容点击事件冒泡
        const modalContent = modal.querySelector('.file-preview-content');
        modalContent.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    function getFilePreviewContent(file) {
        const mimeType = file.mime_type.toLowerCase();

        if (mimeType.startsWith('image/')) {
            return `<img src="${file.file_url}" alt="${file.file_name}" class="file-preview-image" onerror="this.style.display='none'; this.parentElement.innerHTML='<div class=\\'file-preview-generic\\'><svg viewBox=\\'0 0 24 24\\'><path fill=\\'currentColor\\' d=\\'M19 5v14H5V5h14m0-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-4.86 8.86l-3 3.87L9 13.14 6 17h12l-3.86-5.14z\\'/></svg><p>Image preview not available</p><p>Download to view the file</p></div>';" />`;
        }
        else if (mimeType === 'text/plain') {
            // 对于文本文件，尝试加载内容
            return `<div class="file-preview-text">Loading text content...</div>`;
        }
        else if (mimeType === 'application/pdf') {
            return `<div class="file-preview-generic">
                <svg viewBox="0 0 24 24">
                    <path fill="currentColor" d="M20 2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8.5 7.5c0 .83-.67 1.5-1.5 1.5H9v2H7.5V7H10c.83 0 1.5.67 1.5 1.5v1zm5 2c0 .83-.67 1.5-1.5 1.5h-2.5V7H15c.83 0 1.5.67 1.5 1.5v3zm4-3H19v1h1.5V11H19v2h-1.5V7h3v1.5zM9 9.5h1v-1H9v1zM4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm10 5.5h1v-3h-1v3z"/>
                </svg>
                <p>PDF preview not available</p>
                <p>Download to view the file</p>
            </div>`;
        }
        else {
            return `<div class="file-preview-generic">
                <svg viewBox="0 0 24 24">
                    <path fill="currentColor" d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/>
                </svg>
                <p>Preview not available for this file type</p>
                <p>Download to view the file</p>
            </div>`;
        }
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function formatFileTime(timestamp) {
        const date = new Date(timestamp);
        if (Number.isNaN(date.getTime())) {
            return 'Unknown';
        }
        // 转换为北京时间 (UTC+8) 并格式化为 yy-mm-dd
        const beijingDate = new Date(date.getTime() + 8 * 60 * 60 * 1000);
        const year = beijingDate.getFullYear().toString().slice(-2);
        const month = String(beijingDate.getMonth() + 1).padStart(2, '0');
        const day = String(beijingDate.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&")
            .replace(/</g, "<")
            .replace(/>/g, ">")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});