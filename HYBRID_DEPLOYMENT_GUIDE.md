# Hybrid Architecture Deployment Guide

## 🏗️ Architecture Overview

```
User Browser
    ↓
Vercel (Frontend - Static HTML/JS)
    ↓
Render Web Service (Backend API - Flask)
    ↓
Redis (Upstash - Task Queue & Cache)
    ↓
Render Background Worker (Celery - Heavy Processing)
```

## 📁 Directory Structure

```
ai-learning-path-generator/
├── backend/              # Lightweight Flask API
│   ├── app.py           # Main Flask app
│   ├── routes.py        # API endpoints
│   ├── requirements.txt # Minimal dependencies
│   ├── Procfile         # Render web service config
│   └── Dockerfile       # For local testing
│
├── worker/              # Heavy processing worker
│   ├── celery_app.py    # Celery configuration
│   ├── tasks.py         # Task definitions
│   ├── requirements.txt # All heavy dependencies
│   ├── Procfile         # Render worker config
│   └── Dockerfile       # For local testing
│
├── src/                 # Existing logic (used by worker)
│   ├── learning_path.py
│   ├── ml/
│   ├── data/
│   └── utils/
│
└── frontend/            # (To be created in Phase 2)
    └── ...
```

## 🚀 Local Testing

### Prerequisites
- Docker & Docker Compose installed
- Python 3.10+
- Redis (via Docker or local)

### Step 1: Start Services

```bash
# Start all services (Redis, Backend API, Worker)
docker-compose -f docker-compose.dev.yml up
```

### Step 2: Test API

```bash
# Health check
curl http://localhost:5000/health

# Create a task
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Python Programming",
    "expertise_level": "beginner",
    "duration_weeks": 4,
    "time_commitment": "moderate",
    "goals": "Learn basics"
  }'

# Response: {"task_id": "abc-123-...", "status": "queued"}

# Check status
curl http://localhost:5000/api/status/abc-123-...

# Get result (when complete)
curl http://localhost:5000/api/result/abc-123-...
```

## 🌐 Render Deployment

### Part 1: Deploy Backend API

1. **Create New Web Service**
   - Go to Render Dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub repo
   - Name: `ai-learning-path-api`

2. **Configure Build Settings**
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: (use Procfile)

3. **Environment Variables**
   ```
   REDIS_URL=redis://default:<PASSWORD>@<HOST>:<PORT>/0
   OPENAI_API_KEY=YOUR_OPENAI_API_KEY
   PERPLEXITY_API_KEY=YOUR_PERPLEXITY_API_KEY
   ```

4. **Deploy** → Wait for build

### Part 2: Deploy Worker

1. **Create Background Worker**
   - Click "New +" → "Background Worker"
   - Connect same repo
   - Name: `ai-learning-path-worker`

2. **Configure Build Settings**
   - **Root Directory**: `worker`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: (use Procfile)

3. **Environment Variables** (same as backend + all ML configs)
   ```
   REDIS_URL=redis://default:<PASSWORD>@<HOST>:<PORT>/0
   OPENAI_API_KEY=YOUR_OPENAI_API_KEY
   PERPLEXITY_API_KEY=YOUR_PERPLEXITY_API_KEY
   WANDB_MODE=online
   USE_LOCAL_RERANKER=True
   QUERY_REWRITE_ENABLED=True
   CONTEXTUAL_COMPRESSION_ENABLED=True
   # ... all other configs from .env
   ```

4. **Deploy** → Wait for build

### Part 3: Verify

1. **Check API Health**
   ```
   curl https://ai-learning-path-api.onrender.com/health
   ```

2. **Test Task Creation**
   ```bash
   curl -X POST https://ai-learning-path-api.onrender.com/api/generate \
     -H "Content-Type: application/json" \
     -d '{"topic": "Test", "expertise_level": "beginner", "duration_weeks": 2, "time_commitment": "minimal"}'
   ```

3. **Check Worker Logs**
   - Go to Render Dashboard → Worker service → Logs
   - Should see: "Task received", "Processing...", etc.

## 📊 Cost Breakdown

| Service | Type | Cost |
|---------|------|------|
| Backend API | Render Web Service | $7/month |
| Worker | Render Background Worker | $7/month |
| Redis | Upstash (existing) | FREE |
| Frontend | Vercel (Phase 2) | FREE |
| **Total** | | **$14/month** |

## ✅ Benefits

- ✅ **No Timeouts**: Worker can run for hours
- ✅ **All Features**: Nothing disabled
- ✅ **Better UX**: Instant response + progress updates
- ✅ **Scalable**: Can add more workers easily
- ✅ **Reliable**: API never crashes from heavy processing

## 🔄 Rollback Plan

If anything fails:

```bash
# Switch back to main branch
git checkout main
git push origin main --force

# Render will auto-deploy old version
```

Or use Render's "Rollback" button in dashboard.

## 📝 Next Steps

- [ ] Test locally with docker-compose
- [ ] Deploy backend to Render
- [ ] Deploy worker to Render
- [ ] Create frontend (Phase 2)
- [ ] Connect frontend to backend API
- [ ] Add progress polling UI
