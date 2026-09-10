# AI Learning Path Generator

The AI Learning Path Generator is a Flask + React application for creating personalized learning paths from a user's goals, expertise, preferred learning style, time commitment, and topic. It stores user-specific state in PostgreSQL, performs asynchronous generation through Redis + RQ, and uses Gemini as the active model provider for path generation and assistant responses.

This repository is the current Gemini-era version of the project. The application is still built around the existing Flask, Pydantic v1, LangChain, Chroma, Redis, and PostgreSQL architecture where those components remain required; Gemini is integrated through the REST API using Python `requests`, not the Google SDK.

---

## Table of contents

- Overview
- Current architecture
- Gemini migration
- Environment variables
- Local setup
- Docker development
- API overview
- Authentication and ownership
- Frontend
- RAG and vector search
- Resource search behavior
- Background jobs
- Testing and validation
- Troubleshooting
- Security
- Project structure
- AI provider and dependency notes

---

## Project overview

Users can:

- register and log in
- choose a topic, experience level, learning style, and study time
- generate a personalized learning path
- review milestones, resources, and job-market context
- save and revisit learning paths
- track progress on milestones and resources
- ask follow-up questions about their path through the app chat flow

The active runtime stack in this repository is:

- React + Vite frontend
- Flask API/backend
- PostgreSQL for persisted user and learning data
- Redis + RQ for asynchronous work
- Google Gemini REST API for generation
- local Sentence Transformers + Chroma for vector search and resource retrieval
- Perplexity REST API when configured for resource discovery

---

## Current architecture

The current high-level flow is:

```text
React / Vite frontend
        ↓
Flask REST API
        ↓
Authentication + PostgreSQL
        ↓
RQ + Redis background jobs
        ↓
Learning Path Generator
        ↓
Model Orchestrator
        ↓
Google Gemini REST API
        ↓
Pydantic structured output
        ↓
Redis / PostgreSQL persistence
```

The RAG/resource path is also active:

```text
User query / learning path topic
        ↓
Sentence Transformers embeddings
        ↓
Chroma persistent vector store
        ↓
Document/resource retrieval
        ↓
Resource search / sanitization
        ↓
Perplexity REST (when configured)
        ↓
Deterministic documentation fallback when unavailable
        ↓
Learning path generation and chat context
```

Important notes from the repository:

- The active generation provider is Gemini, not OpenAI.
- `src/ml/model_orchestrator.py` validates that the provider is `gemini`.
- `src/ml/gemini_client.py` calls the Gemini `generateContent` endpoint through `requests` with the API key in the `x-goog-api-key` header.
- The app still keeps older LangChain, Chroma, and Pydantic v1 components where the project depends on them for compatibility.
- The repository does contain legacy or commented OpenAI references, but they are not the active generation path in the current runtime.

---

## Gemini migration

The project has migrated from OpenAI as the active generation provider to Google Gemini.

Current repository facts:

- `src/utils/config.py` reads `GEMINI_API_KEY` and `GEMINI_MODEL`.
- `src/ml/model_orchestrator.py` initializes `GeminiClient` and only accepts `provider='gemini'`.
- `src/ml/gemini_client.py` sends HTTP requests to:
  `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`
- The project does not require the `google-genai` Python SDK.
- The direct REST approach is intentional to preserve compatibility with the existing Pydantic v1 and older LangChain stack used elsewhere in the project.

Model configuration found in the repo:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
```

The repository's `.env.example` also sets:

```env
DEFAULT_MODEL=gemini-2.5-flash
```

Security rules:

- Keep `GEMINI_API_KEY` in `.env` or environment variables only.
- Never commit `.env` to version control.
- Never paste API keys into GitHub issues, screenshots, or docs.
- Do not hardcode secrets in code or examples.

---

## Environment variables

The repo expects environment variables from `.env` at the project root. The template is in [.env.example](.env.example).

### Required variables

These are the critical variables a developer needs for a working local app:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
FLASK_SECRET_KEY=replace_with_a_secure_value
DATABASE_URL=postgresql://learning:learning@localhost:5432/learning_path
REDIS_URL=redis://localhost:6379
```

Notes:

- `GEMINI_API_KEY` must be set before generation requests are sent.
- `FLASK_SECRET_KEY` is required by the app config in [`config.py`](config.py).
- `DATABASE_URL` is required because PostgreSQL is the app's persistence layer.
- `REDIS_URL` is required for the RQ worker queue.

### Optional variables

```env
PERPLEXITY_API_KEY=your_perplexity_api_key_here
PERPLEXITY_MODEL=pplx-7b-online
PERPLEXITY_PROMPT_COST_PER_1K=0.0
PERPLEXITY_COMPLETION_COST_PER_1K=0.0
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id_here
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=ai-learning-path-generator
WANDB_API_KEY=your_wandb_api_key_here
WANDB_PROJECT=ai-learning-path-generator
VECTOR_DB_PATH=./vector_db
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
SENTENCE_TRANSFORMER_RESOURCES_COLLECTION=learning_resources_st
SENTENCE_TRANSFORMER_PATHS_COLLECTION=learning_paths_st
FRONTEND_URL=http://localhost:3000
FRONTEND_ORIGIN=http://localhost:3000
```

### Development-only variables

```env
FLASK_APP=run.py
FLASK_ENV=development
DEBUG=True
ENABLE_MOCK_DATA=False
DEV_MODE=False
```

These are not required for the active architecture but are used in local dev and test flows.

---

## Local setup

### Python and environment

The repo includes:

- [runtime.txt](runtime.txt) with `python-3.11.9`
- Dockerfiles based on `python:3.10-slim`

Use a compatible Python 3.10/3.11 environment for local development.

Create and activate a virtual environment:

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Frontend setup

Install frontend dependencies and start the Vite dev server:

```bash
cd frontend
npm install
npm run dev
```

The dev server is configured in [frontend/vite.config.js](frontend/vite.config.js) to run on port `3000` and proxy `/api`, `/auth`, and `/health` to the Flask backend.

### Environment file setup

From the repo root:

```bash
cp .env.example .env
```

Then edit `.env` and set at minimum:

- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `FLASK_SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`

### PostgreSQL and Redis

The repo includes a local development Compose file and uses PostgreSQL + Redis as first-class services.

Create the database and start Redis/PostgreSQL locally with Docker Compose:

```bash
docker compose -f docker-compose.dev.yml up -d postgres redis
```

If you are not using Docker, ensure PostgreSQL is running and a Redis instance is reachable via `DATABASE_URL` and `REDIS_URL`.

### Database initialization

The project includes SQLAlchemy + Flask-Migrate patterns and migration files under [migrations](migrations).

Common startup paths:

```bash
python run.py
```

This script also creates a `.env` file from `.env.example` if missing, then initializes the Flask app.

### Backend startup

The main Flask app is created in [web_app/__init__.py](web_app/__init__.py) and started with:

```bash
python run.py
```

The backend listens on port `5000` by default.

### Worker startup

The worker uses Redis Queue to process background jobs:

```bash
python worker.py
```

This script listens on the `learning-paths` queue and is the repository's worker entrypoint.

### Frontend startup

From [frontend](frontend):

```bash
cd frontend
npm run dev
```

The frontend expects the API at `http://localhost:5000` by default and uses Vite proxying to keep the browser on port `3000`.

---

## Docker development

The current Compose file is [docker-compose.dev.yml](docker-compose.dev.yml). It defines four main services:

### Services

- `postgres`: PostgreSQL 16 with the database `learning_path`
- `redis`: Redis 7 for the RQ queue
- `backend`: Flask app container
- `worker`: RQ worker container

### Start command

```bash
docker compose -f docker-compose.dev.yml up --build
```

The `backend` service:

- builds from [backend/Dockerfile](backend/Dockerfile)
- exposes port `5000`
- sets `DATABASE_URL` and `REDIS_URL` to the Compose service names
- loads environment variables from `.env`

The `worker` service:

- builds from [worker/Dockerfile](worker/Dockerfile)
- installs the worker dependencies
- runs the root-level [worker.py](worker.py) entrypoint

Service health is checked for Postgres and Redis before the backend starts.

---

## API overview

The active API surface is primarily JSON and uses Flask-Login session auth.

### Authentication and session APIs

| Method | Route | Purpose | Auth |
| --- | --- | --- | --- |
| `POST` | `/api/auth/register` | Create a new local user account and log in | No |
| `POST` | `/api/auth/login` | Log in with email/password | No |
| `POST` | `/api/auth/logout` | Log out and clear the session | No |
| `GET` | `/api/auth/me` | Return current authenticated user info | No, but returns unauthenticated state if not logged in |
| `GET` | `/api/me` | Return current authenticated user info | No, but returns unauthenticated state if not logged in |

### Learning path and progress APIs

| Method | Route | Purpose | Auth |
| --- | --- | --- | --- |
| `POST` | `/api/generate` | Queue a path-generation task | Yes |
| `GET` | `/api/status/<task_id>` | Poll task status | Yes |
| `GET` | `/api/result/<task_id>` | Fetch final learning-path result | Yes |
| `GET` | `/api/paths` | List saved learning paths for the current user | Yes |
| `GET` | `/api/paths/<path_id>` | Fetch one saved path and its progress | Yes |
| `POST` | `/api/save-path` | Save a generated path to the user's record | Yes |
| `POST` | `/api/track-milestone` | Update milestone completion status | Yes |
| `POST` | `/api/ask` | Ask a contextual question about a path | Yes |
| `GET` | `/health` | Backend health / database connectivity check | No |

The repository also contains an alternate `generate-task` and `task-status` flow in [web_app/main_routes.py](web_app/main_routes.py), but the active frontend and backend route implementations in [backend/routes.py](backend/routes.py) and [frontend/src/lib/api.js](frontend/src/lib/api.js) use the `/api/generate`, `/api/status/<task_id>`, and `/api/result/<task_id>` pattern.

---

## Authentication and ownership

Authentication is handled by Flask-Login and session cookies.

Current repository behavior:

- `web_app/models.py` defines the `User` model and `UserLearningPath` model.
- `web_app/auth_api.py` exposes the JSON register/login/logout endpoints used by React.
- `web_app/__init__.py` initializes `LoginManager` and returns JSON 401 responses for unauthenticated API calls instead of HTML redirects.
- `UserLearningPath` rows are tied to a specific `user_id`.
- All path-fetching and progress writes enforce `current_user.id` ownership checks before returning or updating records.

This means users can only view or modify their own learning paths and their own milestone/progress records. Unauthorized access is handled at the application layer by filtering on `user_id` and returning `404` or `401` responses depending on the endpoint.

---

## Frontend

The frontend is a React + Vite app under [frontend](frontend), with a dev server on port `3000` and an API proxy defined in [frontend/vite.config.js](frontend/vite.config.js).

Relevant package details from [frontend/package.json](frontend/package.json):

- React 18
- Vite 5
- Axios for API calls
- Tailwind CSS and Vite plugins for styling
- lucide-react icons

The frontend dev behavior:

- browser calls are mostly same-origin via `/api`
- the Vite server proxies `'/api'`, `'/auth'`, and `'/health'` to the Flask backend on port `5000`
- session cookies are sent with credentials so the Flask auth session is preserved between refreshes

The primary user journey in the app is:

1. registration or login
2. generate a learning path
3. poll task status
4. fetch final result
5. save and view the path
6. update milestone progress and ask chat questions

---

## RAG / vector search

The current vector-search architecture uses local Sentence Transformers embeddings with Chroma persistence.

Actual configuration values found in [src/utils/config.py](src/utils/config.py):

```env
VECTOR_DB_PATH=./vector_db
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
SENTENCE_TRANSFORMER_RESOURCES_COLLECTION=learning_resources_st
SENTENCE_TRANSFORMER_PATHS_COLLECTION=learning_paths_st
```

The embedding function is implemented in [src/ml/local_embeddings.py](src/ml/local_embeddings.py):

- `SentenceTransformerEmbeddingFunction`
- wraps `sentence_transformers.SentenceTransformer`
- uses `normalize_embeddings=True`
- returns vectors in the model's native embedding dimension

The repo does not define an explicit fixed embedding dimension constant, so the exact output dimension is not enforced as a single project-wide variable. The model used is clearly `all-MiniLM-L6-v2`.

The vector store is initialized in [src/data/document_store.py](src/data/document_store.py):

- Chroma persistent store at `./vector_db`
- shared singleton client
- collection names default to `learning_resources_st` and `learning_paths_st`
- embedding provider metadata is preserved as `sentence-transformers`

The project intentionally keeps older vector data and adds new Sentence Transformer collections without blindly deleting existing Chroma state. The index utility in [src/data/index_sentence_transformers.py](src/data/index_sentence_transformers.py) explicitly skips existing IDs and does not delete previous collections.

The document store is used for context retrieval in chat and learning-path generation. Search calls are made through `DocumentStore` and the generative flow can augment prompts with relevant documents before generating a response.

---

## Resource search

Resource discovery is implemented in [src/ml/resource_search.py](src/ml/resource_search.py).

Current behavior:

- If `PERPLEXITY_API_KEY` is configured, the app calls the Perplexity chat-completions endpoint with `requests`.
- It validates, sanitizes, and deduplicates resource URLs before returning them.
- It rejects malformed or placeholder values such as `example.com` and `Configure Perplexity...` strings.
- If the API is missing, returns an error, or produces unusable data, the app falls back to deterministic real documentation resources instead of placeholder URLs.
- Links are filtered to real documentation pages and safe external resources.

The fallback is not fake placeholder URLs. It points to real, authoritative documentation such as:

- Python docs
- MDN docs
- PostgreSQL docs
- Redis docs
- Docker docs
- Flask docs
- scikit-learn docs

The repository also contains frontend safe-link handling patterns for external resources; this is not a code change request but the app is expected to render external resource links with safe `target`/`rel` handling.

---

## Background jobs

The asynchronous generation flow uses Redis + RQ.

Repository details:

- `worker.py` creates the Redis connection and starts `rq.Worker` on the `learning-paths` queue.
- `worker/tasks.py` defines `generate_learning_path_for_worker(payload)` as the background worker task.
- `backend/routes.py` and `web_app/main_routes.py` enqueue jobs using `Queue('learning-paths', connection=...)`.
- The same queue is used to generate learning paths without blocking the UI request.

Worker startup command:

```bash
python worker.py
```

The project also includes a Docker Compose worker service that runs the same worker in the containerized dev setup.

---

## Testing and validation

The repository includes actual pytest checks, especially around resource-search behavior in [tests/test_resource_search.py](tests/test_resource_search.py).

Run the test suite from the repo root:

```bash
pytest
```

For frontend validation if dependencies are installed:

```bash
cd frontend
npm run build
npm run lint
```

The repository appears to have a focused test suite rather than comprehensive end-to-end coverage. The test files include resource fallback and sanitization checks rather than a large full-stack suite.

---

## Troubleshooting

### Missing Gemini API key

If generation fails with a Gemini credential error, confirm the `.env` file includes:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
```

and that it is not committed or leaked in the repo.

### Model configuration problems

If the app cannot generate a response, verify that the configured model name matches a valid Gemini model and that your API key is valid.

### Backend or worker not running

Check:

- PostgreSQL is reachable on `DATABASE_URL`
- Redis is reachable on `REDIS_URL`
- the backend has been started with `python run.py`
- the worker has been started with `python worker.py`

### Redis/PostgreSQL unavailable

The Compose stack starts both services automatically. If local services fail, use:

```bash
docker compose -f docker-compose.dev.yml up -d postgres redis
```

### Docker services not healthy

Check health status with Docker Compose and ensure the Postgres and Redis checks pass before the backend starts.

### Frontend cannot reach API

Verify:

- the backend is running on port `5000`
- Vite proxy is configured in [frontend/vite.config.js](frontend/vite.config.js)
- the browser is visiting `http://localhost:3000` rather than directly hitting `5000`

### Resource search fallback activated

If `PERPLEXITY_API_KEY` is missing or invalid, the app will fall back to deterministic resource URLs from the repository's resource library. This is expected behavior and not a placeholder failure state.

### Vector/RAG dependency issues

If Sentence Transformers or Chroma initialization fails, verify the Python environment has installed the dependencies from [requirements.txt](requirements.txt), especially:

- `sentence-transformers`
- `chromadb`
- `numpy`
- `scikit-learn`

---

## Security

- Never commit `.env` files.
- Never expose `GEMINI_API_KEY` or other secrets in GitHub, screenshots, logs, or docs.
- The app authenticates API calls via Flask-Login sessions.
- User data and saved learning paths are isolated by `user_id` in PostgreSQL.
- Resource URLs are sanitized and validated before use.
- External resource links should be rendered with safe `target`/`rel` handling, as the project expects.
- Do not paste API keys into issues or support threads.

---

## Project structure

```text
ai-learning-path-generator/
├── .env.example
├── .gitignore
├── README.md
├── config.py
├── docker-compose.dev.yml
├── requirements.txt
├── runtime.txt
├── run.py
├── worker.py
├── backend/
│   ├── Dockerfile
│   ├── app.py
│   ├── requirements.txt
│   └── routes.py
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
├── web_app/
│   ├── __init__.py
│   ├── api_endpoints.py
│   ├── auth_api.py
│   ├── auth_forms.py
│   ├── auth_routes.py
│   ├── google_oauth.py
│   ├── main_routes.py
│   ├── models.py
│   └── routes/
├── src/
│   ├── data/
│   ├── ml/
│   ├── services/
│   ├── utils/
│   ├── agent.py
│   ├── learning_path.py
│   └── direct_openai.py
├── worker/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── tasks.py
│   └── __init__.py
├── migrations/
├── vector_db/
├── tests/
├── docs/
└── ...
```

This reflects the repository layout that is actually present. The project does include additional documentation files and migration scripts beyond the baseline structure above.

---

## AI provider and dependency notes

The active AI provider is Gemini through the REST API. The project deliberately does not depend on the `google-genai` Python SDK.

The app also intentionally preserves a Pydantic v1, LangChain, Chroma, and Flask environment where required by the existing system. The migration is deliberately additive and compatibility-oriented rather than a rewrite of the whole stack.

Important dependency details from [requirements.txt](requirements.txt):

- `pydantic==1.10.18`
- `langchain==0.0.267`
- `chromadb==0.3.29`
- `sentence-transformers>=2.2.2`
- `rq==1.16.1`
- `Flask-Login==0.6.3`

Legacy OpenAI references remain in a few compatibility or historical files, but they are not the active generation provider in the current code path. The active runtime is configured for Gemini via `GeminiClient` and `ModelOrchestrator`.

---

## Summary

This project is a full-stack AI learning app with:

- a Vite/React frontend
- a Flask API with session-based auth
- PostgreSQL-backed ownership and persistence
- Redis/RQ background generation tasks
- Gemini REST generation
- local Sentence Transformer + Chroma retrieval
- Perplexity-backed resource search when configured
- deterministic fallback learning resources when external APIs are unavailable

The repository is currently a Gemini-based, compatibility-preserving architecture rather than a clean OpenAI-only implementation.
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
