# Agentic Tutor [中文](readme_chinese.md)

An AI-powered educational platform designed to support Chinese children in their learning journey with personalized tutoring.

## Project Overview

Agentic Tutor is an intelligent tutoring system that leverages AI agents to provide personalized learning experiences for children. The system combines advanced AI models with user profiles to create adaptive learning interactions.

## Features

- **Personalized Learning**: Each user has customizable personas that shape the AI tutor's teaching style and approach
- **Chat Interface**: Streamlined chat interface for engaging with the AI tutor
- **User Authentication**: Secure login system with JWT token authentication
- **Session Management**: Persistent chat sessions to maintain context and continuity
- **Responsive Design**: Modern, child-friendly UI with dark mode support

## Technology Stack

- **Backend**: FastAPI for building the RESTful API
- **Database**: SQLite with async support for data persistence
- **AI Integration**: Agentscope with DashScope for AI model integration
- **Frontend**: HTML, CSS, and JavaScript with modern UI components
- **Authentication**: JWT token-based authentication system

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/v587d/Agentic-Tutor.git "Agentic Tutor"
   cd "Agentic Tutor"
   ```

2. Install dependencies:

   ```bash
   uv pip install -r pyproject.toml
   ```

3. Set up environment variables:
   Create a `.env` file in the project root and add:

   ```
   PYTHONPATH=.
   API_KEY=your_BAILIAN_api_key_here
   SECRET_KEY=your_secret_key_here
   ACCESS_TOKEN_EXPIRE_MINUTES=120
   ```

4. Initialize the database:

   ```bash
   python -m src.api
   ```

## Usage

1. Start the server:

   ```bash
   python -m src.api
   ```

2. Access the application at `http://localhost:8000`

3. Sign up or log in to create an account

4. Create and customize your learning persona

5. Start chatting with your AI tutor!

## API Endpoints

- `/chat/stream`: Stream chat responses with the AI tutor
- `/user/register`: Register a new user
- `/user/login`: User login
- `/user/me`: Get current user information
- `/user/persona`: Manage user personas
- `/user/persona/{persona_id}`: Get, update, or delete specific personas

## Project Structure

```
Agentic-Tutor/
├── src/
│   ├── agents/          # AI agent implementations
│   ├── api/             # FastAPI application and routes
│   ├── config/          # Configuration settings
│   ├── db/              # Database models and connections
│   ├── repositories/    # Data access layer
│   ├── schemas/         # Pydantic models for API validation
│   └── utils/           # Utility functions
├── static/              # Static frontend assets
└── database/            # SQLite database files
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
