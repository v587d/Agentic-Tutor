let isLoginMode = true;
const LOGIN = '/user/login'
const SIGNUP = '/user/register'

// Handle signup link click
document.getElementById('signupLink').addEventListener('click', function (e) {
    e.preventDefault();
    switchToSignup();
});

// Handle back to login
document.getElementById('backLink').addEventListener('click', function (e) {
    e.preventDefault();
    switchToLogin();
});

function switchToSignup() {
    isLoginMode = false;
    document.getElementById('pageTitle').textContent = 'Create Account';
    document.getElementById('submitBtn').textContent = 'Start Chatting';
    document.getElementById('slogan').style.display = 'none';
    document.getElementById('email').placeholder = 'Email address';
    document.getElementById('password').placeholder = 'Password';
    document.getElementById('authLinks').style.display = 'none';
    document.getElementById('backToLogin').style.display = 'flex';
    document.getElementById('backToChat').style.display = 'none';
    clearMessages(); // 清除提示
}

function switchToLogin() {
    isLoginMode = true;
    document.getElementById('pageTitle').textContent = 'Kids AI Tutor';
    document.getElementById('submitBtn').textContent = 'Continue';
    document.getElementById('slogan').style.display = 'block';
    document.getElementById('email').placeholder = 'Email';
    document.getElementById('password').placeholder = 'Password';
    document.getElementById('authLinks').style.display = 'flex';
    document.getElementById('backToLogin').style.display = 'none';
    document.getElementById('backToChat').style.display = 'block';
    clearMessages(); // 清除提示
}

// Form submission
document.getElementById('authForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    clearMessages(); // 清除旧提示

    // 验证密码长度
    if (!validatePassword(password)) {
        showError('Password: 8–20 characters.');
        return;
    }

    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Processing...';

    try {
        const endpoint = isLoginMode ? LOGIN : SIGNUP;
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: email,  // 注意后端使用username而不是email
                password: password
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Authentication failed');
        }

        // 保存token到localStorage
        if (data.access_token) {
            localStorage.setItem('access_token', data.access_token);
        }

        // showSuccess(isLoginMode ? 'Login successful!' : 'Registration successful!');
        // 成功时直接在按钮中显示
        submitBtn.textContent = '✅ Ready? GO!';
        // 登录成功后跳转到首页
        setTimeout(() => {
            window.location.href = '/';
        }, 1500);

    } catch (error) {
        showError(error.message || 'An error occurred. Please try again.');
        // 只在出错时重置按钮状态
        submitBtn.disabled = false;
        submitBtn.textContent = isLoginMode ? 'Continue' : 'Start Chatting';
    }
});

// 验证密码长度8-20位之间
function validatePassword(password) {
    return password.length >= 8 && password.length <= 20;
}

// 清除所有消息
function clearMessages() {
    const existingError = document.querySelector('.error-message');
    const existingSuccess = document.querySelector('.success-message');
    if (existingError) existingError.remove();
    if (existingSuccess) existingSuccess.remove();
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = false;
    submitBtn.style.background = ''; // 重置按钮样式
}

// 显示成功消息
function showSuccess(message) {
    clearMessages();
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.textContent = message;

    const form = document.getElementById('authForm');
    const submitBtn = document.getElementById('submitBtn');
    form.insertBefore(successDiv, submitBtn);

    const submitBtnEl = document.getElementById('submitBtn');
    submitBtnEl.disabled = true; // 禁用按钮防止重复点击

    // 5秒后移除（成功消息持续时间）
    setTimeout(() => {
        successDiv.remove();
        submitBtnEl.disabled = false;
    }, 5000);
}

// 显示错误消息
function showError(message) {
    clearMessages();

    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;

    const form = document.getElementById('authForm');
    const submitBtn = document.getElementById('submitBtn');
    form.insertBefore(errorDiv, submitBtn);

    // 5秒后移除
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}




