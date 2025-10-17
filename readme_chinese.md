# Agentic Tutor

一个支持中国儿童快乐成长的AI智能教育平台。

## 项目概述

Agentic Tutor 是一个智能辅导系统，利用AI代理为儿童提供个性化的学习体验。该系统结合先进的AI模型与用户画像，创建自适应的学习互动。

## 功能特点

- **个性化学习**：每个用户都有可定制的角色画像，塑造AI辅导者的教学风格和方法
- **聊天界面**：简洁的聊天界面，方便与AI辅导者互动
- **用户认证**：基于JWT令牌的安全登录系统
- **会话管理**：持久化的聊天会话，保持上下文和连续性
- **响应式设计**：现代化、儿童友好的用户界面，支持深色模式

## 技术栈

- **后端**：FastAPI 构建RESTful API
- **数据库**：支持异步的SQLite
- **AI集成**：Agentscope与DashScope进行AI模型集成
- **前端**：HTML、CSS和JavaScript，带有现代化UI组件
- **认证**：基于JWT令牌的认证系统

## 安装

1. 克隆仓库：

   ```bash
   git clone <仓库地址>
   cd Agentic-Tutor
   ```

2. 安装依赖：

   ```bash
   uv pip install -r pyproject.toml
   ```

3. 设置环境变量：
   在项目根目录创建 `.env` 文件并添加：

   ```
   PYTHONPATH=.
   API_KEY=your_BAILIAN_api_key_here
   SECRET_KEY=your_secret_key_here
   ACCESS_TOKEN_EXPIRE_MINUTES=120
   ```

4. 初始化数据库：

   ```bash
   python -m src.api
   ```

## 使用方法

1. 启动服务器：

   ```bash
   python -m src.api
   ```

2. 访问应用 `http://localhost:8000`

3. 注册或登录创建账户

4. 创建并定制你的学习角色画像

5. 开始与你的AI辅导者聊天！

## API端点

- `/chat/stream`：获取AI辅导者的流式聊天响应
- `/user/register`：注册新用户
- `/user/login`：用户登录
- `/user/me`：获取当前用户信息
- `/user/persona`：管理用户角色画像
- `/user/persona/{persona_id}`：获取、更新或删除特定角色画像

## 项目结构

```
Agentic-Tutor/
├── src/
│   ├── agents/          # AI代理实现
│   ├── api/             # FastAPI应用和路由
│   ├── config/          # 配置设置
│   ├── db/              # 数据库模型和连接
│   ├── repositories/    # 数据访问层
│   ├── schemas/         # API验证的Pydantic模型
│   └── utils/           # 工具函数
├── static/              # 静态前端资源
└── database/            # SQLite数据库文件
```

## 贡献

欢迎贡献！请随时提交Pull Request。

## 许可证

本项目采用MIT许可证 - 详情请参阅[LICENSE](LICENSE)文件。
