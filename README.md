# AI Learning Path Generator 🚀

An AI-powered learning path generator that creates personalized learning roadmaps based on a user's learning goals, experience level, preferred learning style, and available study time.

The project uses a modern **React + Vite Liquid Glass frontend**, a **Flask REST API backend**, **PostgreSQL** for persistent data, and **Redis/RQ** for background learning-path generation jobs.

---

## ✨ Features

### 🤖 AI-Powered Learning Path Generation

- Generate personalized learning paths using OpenAI
- Choose your expertise level
- Define your learning goals
- Select your preferred learning style
- Specify available study time
- Generate structured learning milestones
- Get recommended learning resources
- Receive career and job-market insights
- Track learning progress

### 👤 User Authentication

- User registration with email and password
- Secure login/logout
- Persistent user sessions
- Session restoration after page refresh
- Google OAuth integration
- User-specific data isolation
- Server-side authentication and authorization

### 💾 Persistent Learning Data

Authenticated users can save and manage:

- Learning paths
- Milestones
- Learning progress
- Completed resources
- User-specific learning information

User data is stored in PostgreSQL and is protected by server-side ownership checks.

### 💬 AI Assistant

The application includes an AI-powered assistant that can help with:

- General learning questions
- Learning-path creation
- Learning-path modification
- Research
- Skills and career discussions
- Job-market related questions

### 📊 Learning Progress

The application provides progress tracking for generated learning paths.

Users can:

- Mark resources as completed
- Track milestone progress
- Continue previously generated paths
- View saved learning paths

### ⚡ Background Generation

Learning-path generation uses a background job architecture:

```text
React Frontend
      ↓
Flask API
      ↓
Redis / RQ Queue
      ↓
Background Worker
      ↓
OpenAI API
      ↓
PostgreSQL
      ↓
React Frontend
```

This prevents long-running AI generation tasks from blocking the frontend.

---

# 🎨 Liquid Glass UI

The application uses a modern dark **Liquid Glass** design system.

### Design characteristics

- Dark / black background
- Glassmorphism
- Transparent glass surfaces
- Backdrop blur
- Soft borders
- High-contrast typography
- White and light-colored text
- Subtle gradients
- Smooth animations
- Responsive layouts
- Modern interactive components

The React frontend is the **only user-facing application**.

Flask is used as the backend/API layer.

---

# 🏗️ Architecture

```text
                         USER
                           │
                           ▼
              ┌─────────────────────────┐
              │     React Frontend      │
              │                         │
              │       Vite              │
              │       Tailwind CSS      │
              │       Liquid Glass UI   │
              │                         │
              │    localhost:3000       │
              └────────────┬────────────┘
                           │
                           │ REST API
                           ▼
              ┌─────────────────────────┐
              │      Flask Backend      │
              │                         │
              │    localhost:5000       │
              │                         │
              │  Authentication         │
              │  Learning Paths         │
              │  Progress               │
              │  Chat                   │
              │  API Endpoints          │
              └────────────┬────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        PostgreSQL      Redis/RQ      OpenAI
        Database        Queue         API
              │            │
              │            ▼
              │       Background
              │         Worker
              │
              ▼
       Persistent User
       & Learning Data
```

---

# 🧰 Technology Stack

## Frontend

- React
- Vite
- Tailwind CSS
- Axios
- Lucide React
- React Router
- Liquid Glass UI

## Backend

- Python
- Flask
- Flask-Login
- SQLAlchemy
- Flask-Migrate
- Flask-WTF
- Google OAuth
- REST APIs

## AI / ML

- OpenAI API
- LangChain
- Pydantic
- ChromaDB
- FAISS
- Sentence Transformers
- scikit-learn
- NumPy
- pandas

## Database

- PostgreSQL
- SQLAlchemy ORM
- Flask-Migrate / Alembic

## Background Processing

- Redis
- RQ / background worker

## Infrastructure

- Docker
- Docker Compose

## Testing

- pytest
- ESLint
- Vite production build
- Python compile checks

---

# 📁 Project Structure

```text
ai-learning-path-generator/
│
├── frontend/
│   ├── src/
│   │   ├── auth/
│   │   ├── components/
│   │   ├── lib/
│   │   ├── pages/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   │
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── .env.example
│
├── backend/
│   ├── app.py
│   ├── routes.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── Procfile
│
├── web_app/
│   ├── __init__.py
│   ├── app.py
│   ├── api_endpoints.py
│   ├── api_auth.py
│   ├── auth_forms.py
│   ├── auth_routes.py
│   ├── google_oauth.py
│   ├── frontend.py
│   ├── main_routes.py
│   ├── models.py
│   └── routes/
│
├── src/
│   ├── agent.py
│   ├── learning_path.py
│   ├── direct_openai.py
│   ├── agents/
│   ├── data/
│   ├── ml/
│   ├── services/
│   └── utils/
│
├── worker/
│   ├── celery_app.py
│   ├── tasks.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── Procfile
│
├── migrations/
├── tests/
├── tools/
├── vector_db/
├── learning_paths/
│
├── docker-compose.dev.yml
├── Dockerfile
├── requirements.txt
├── config.py
├── run.py
├── run_flask.py
├── .env.example
├── .gitignore
└── README.md
```

---

# 🚀 Getting Started

## Prerequisites

Make sure you have installed:

- Python 3.10+
- Node.js 18+
- npm
- Docker Desktop
- Git

You also need an OpenAI API key for AI-powered learning-path generation.

---

# 1. Clone the Repository

```bash
git clone https://github.com/amlan-13767/ai-learning-path-generator.git

cd ai-learning-path-generator
```

---

# 2. Configure Environment Variables

Create your local environment file.

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### macOS / Linux

```bash
cp .env.example .env
```

Then configure your environment variables.

Example:

```env
OPENAI_API_KEY=your_openai_api_key_here

FLASK_SECRET_KEY=your_secret_key_here

DATABASE_URL=postgresql://postgres:postgres@postgres:5432/learning_path

REDIS_URL=redis://redis:6379/0
```

For Google OAuth:

```env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

### Security

Never commit your `.env` file.

Never put API keys, OAuth secrets, database passwords, or other credentials inside source code.

---

# 3. Start Backend Services

From the repository root:

```powershell
docker compose -f docker-compose.dev.yml up --build
```

This starts the backend infrastructure required by the application.

Depending on the Docker configuration, the services include:

- Flask backend
- PostgreSQL
- Redis
- Background worker

The backend API is available at:

```text
http://localhost:5000
```

The backend is API-only.

The React application is the user-facing interface.

---

# 4. Start the React Frontend

Open a **second terminal**.

From the repository root:

```powershell
cd frontend
```

Install frontend dependencies:

```powershell
npm install
```

Start the development server:

```powershell
npm run dev
```

The frontend will be available at:

```text
http://localhost:3000
```

---

# ⚠️ Important: Use localhost

For local development, use:

```text
http://localhost:3000
```

instead of:

```text
http://127.0.0.1:3000
```

This is especially important when testing authentication and Google OAuth because browser cookies and OAuth redirects depend on consistent hosts.

---

# 🔐 Authentication

Authentication is handled by Flask and PostgreSQL.

The React frontend communicates with authentication APIs.

## Register

```http
POST /api/auth/register
```

## Login

```http
POST /api/auth/login
```

## Logout

```http
POST /api/auth/logout
```

## Restore Session

```http
GET /api/auth/me
```

## Current User

```http
GET /api/me
```

The application uses server-side authentication and authorization.

User-specific resources are protected so that one user cannot access another user's learning paths or progress.

---

# 🔑 Google OAuth

Google OAuth integration is supported by the Flask backend.

The general authentication flow is:

```text
React Frontend
      │
      ▼
Flask OAuth Endpoint
      │
      ▼
Google Authentication
      │
      ▼
Flask Session
      │
      ▼
React Frontend
```

For local development, keep the host consistent:

```text
http://localhost:3000
```

Do not switch between `localhost` and `127.0.0.1` while testing the authentication flow.

---

# 🧠 Learning Path Generation

The learning-path generation process works approximately as follows:

```text
User enters learning requirements
              │
              ▼
       React Frontend
              │
              ▼
       POST /api/generate
              │
              ▼
        Flask Backend
              │
              ▼
        Redis / RQ Queue
              │
              ▼
       Background Worker
              │
              ▼
          OpenAI API
              │
              ▼
    Structured AI Response
              │
              ▼
      Validation / Processing
              │
              ▼
        PostgreSQL
              │
              ▼
       React Frontend
              │
              ▼
       Learning Path
```

---

# 📊 Generation Status

After a generation request is submitted, the frontend can check the status of the background task.

```http
GET /api/status/<task_id>
```

Once generation is completed:

```http
GET /api/result/<task_id>
```

The generated learning path is then displayed in the React application.

---

# 🔌 API Endpoints

Important API endpoints include:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/auth/register` | POST | Register a new user |
| `/api/auth/login` | POST | Authenticate a user |
| `/api/auth/logout` | POST | End the current session |
| `/api/auth/me` | GET | Restore the current session |
| `/api/me` | GET | Retrieve current user information |
| `/api/generate` | POST | Start learning-path generation |
| `/api/status/<task_id>` | GET | Check generation status |
| `/api/result/<task_id>` | GET | Retrieve generated result |
| `/api/paths` | GET | Retrieve user's learning paths |
| `/api/progress` | GET/POST | Manage learning progress |
| `/api/chat` | POST | Interact with AI assistant |

---

# 💾 Data Persistence

The application uses PostgreSQL for persistent data storage.

Authenticated users can save their learning paths and progress.

Example data includes:

```text
User
 │
 ├── Learning Path 1
 │      ├── Milestone 1
 │      ├── Milestone 2
 │      └── Resources
 │
 ├── Learning Path 2
 │      ├── Milestone 1
 │      └── Resources
 │
 └── Progress
```

All user-owned resources are checked server-side before being returned or modified.

---

# 💬 AI Assistant

The application includes an AI assistant integrated into the React interface.

The assistant can be used for:

### General Chat

Ask questions related to:

- Programming
- AI
- Machine learning
- Learning strategies
- Education

### Path Creation

Users can describe what they want to learn conversationally.

Example:

```text
Create a learning path for machine learning
for an intermediate Python developer.
```

### Research

The assistant can help explore:

- Skills
- Career paths
- Job-market information
- Learning resources
- Related technologies

---

# 🗄️ Database

The project uses PostgreSQL for persistent application data.

Database functionality includes:

- User accounts
- Authentication data
- Learning paths
- Learning progress
- Resource completion
- User ownership

Database migrations are managed using Flask-Migrate / Alembic.

---

# 🐳 Docker

The project provides Docker configuration for local development.

## Start

```powershell
docker compose -f docker-compose.dev.yml up --build
```

## Stop

```powershell
docker compose -f docker-compose.dev.yml down
```

## Stop and remove volumes

```powershell
docker compose -f docker-compose.dev.yml down -v
```

> Warning: removing Docker volumes can delete local PostgreSQL data.

---

# 🧪 Testing

## Frontend Lint

From the repository root:

```powershell
cd frontend

npm run lint
```

---

## Frontend Production Build

```powershell
npm run build
```

---

## Python Compilation Check

From the repository root:

```powershell
python -m compileall .
```

---

## Run Python Tests

```powershell
python -m pytest tests/
```

---

# 🛠️ Development Workflow

For normal local development, use two terminals.

## Terminal 1 — Backend

From the repository root:

```powershell
docker compose -f docker-compose.dev.yml up --build
```

## Terminal 2 — Frontend

```powershell
cd frontend

npm run dev
```

Then open:

```text
http://localhost:3000
```

---

# 🌐 Application URLs

### React Frontend

```text
http://localhost:3000
```

### Flask Backend API

```text
http://localhost:5000
```

The React application is the main user interface.

The Flask server provides backend APIs and services.

---

# 🎨 Design System

The current frontend uses a dark Liquid Glass design.

## Main Design Principles

```text
Dark Background
       +
Transparent Glass
       +
Backdrop Blur
       +
Soft Borders
       +
High Contrast Text
       +
Subtle Animations
       =
Liquid Glass UI
```

### UI characteristics

- Dark black background
- Glass cards
- Transparent surfaces
- Blur effects
- Soft shadows
- White/light text
- Minimal neon accents
- Smooth transitions
- Responsive design

---

# 🔒 Security

The application follows several security practices.

### Environment Variables

Secrets are stored in environment variables.

```text
OPENAI_API_KEY
FLASK_SECRET_KEY
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
DATABASE_URL
```

### Never Commit Secrets

Do not commit:

```text
.env
```

to GitHub.

Only commit:

```text
.env.example
```

with placeholder values.

### User Data Isolation

Backend authorization checks ensure users can only access their own protected resources.

---

# ⚠️ OpenAI API

The application currently uses OpenAI for AI-powered learning-path generation.

Configure:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

If the OpenAI account has no available API quota or credits, AI generation may return an API error even when the application itself is configured correctly.

The OpenAI integration is intentionally kept as the current AI provider.

---

# 📦 Frontend Commands

From the `frontend` directory:

## Install dependencies

```powershell
npm install
```

## Development server

```powershell
npm run dev
```

## Lint

```powershell
npm run lint
```

## Production build

```powershell
npm run build
```

## Preview production build

```powershell
npm run preview
```

---

# 📦 Backend Commands

Depending on the development environment, Flask can be run through Docker or directly.

For Docker development:

```powershell
docker compose -f docker-compose.dev.yml up --build
```

For local Python development:

```powershell
python run.py
```

---

# 🧭 Application Flow

A typical user flow is:

```text
1. Open application
        ↓
2. Register / Login
        ↓
3. Build Learning Path
        ↓
4. Submit Requirements
        ↓
5. Background Generation
        ↓
6. AI Processing
        ↓
7. Learning Path Generated
        ↓
8. View Learning Path
        ↓
9. Save Path
        ↓
10. Track Progress
```

---

# 📈 Future Improvements

Possible future improvements include:

- Additional AI model providers
- More learning resource providers
- Advanced career recommendations
- Improved progress analytics
- More personalization options
- Deployment automation
- Enhanced AI tutoring capabilities
- Additional OAuth providers

---

# 🤝 Contributing

Contributions are welcome.

### 1. Fork the repository

### 2. Create a feature branch

```bash
git checkout -b feature/my-feature
```

### 3. Make your changes

### 4. Run tests

```bash
python -m pytest tests/
```

### 5. Check the frontend

```bash
cd frontend
npm run lint
npm run build
```

### 6. Commit your changes

```bash
git add .
git commit -m "Add my feature"
```

### 7. Push your branch

```bash
git push origin feature/my-feature
```

### 8. Open a Pull Request

---

# 👨‍💻 Authors

## Amlan Prateek Panda

- Email: amlanprateeknitr8282@gmail.com
- GitHub: https://github.com/amlan-13767

## Kalpita Saha

- Email: kalpitasaha03@gmail.com
- GitHub: https://github.com/Kolpi03

---

# 🔗 Repository

GitHub Repository:

https://github.com/amlan-13767/ai-learning-path-generator

---

# 📜 License

This project is licensed under the MIT License.

See the `LICENSE` file for details.

---

# 🙏 Acknowledgments

- OpenAI
- LangChain
- Flask
- React
- Vite
- Tailwind CSS
- PostgreSQL
- Redis
- RQ
- ChromaDB
- Sentence Transformers

---

# ❤️ Built With

**Python • Flask • React • Vite • Tailwind CSS • PostgreSQL • Redis • OpenAI • Docker**

Built by **Amlan Prateek Panda** and **Kalpita Saha**.
