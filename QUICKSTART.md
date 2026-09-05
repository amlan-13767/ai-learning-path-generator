# 🚀 Quick Start Guide

Get the AI Learning Path Generator running in minutes!

## 🎯 What You're Building

A full-stack AI application with:
- **React Frontend** (Vercel) - Beautiful glassmorphic UI
- **Flask API** (Render) - Lightweight REST API
- **Background Worker** (Render) - Heavy AI processing
- **Redis** (Redis Cloud) - Queue and cache

## ⚡ Quick Deploy (Production)

### 1. Backend API + Worker (15 minutes)

**Prerequisites:**
- GitHub account
- Render account (free)
- Redis Cloud account (free)
- OpenAI API key

**Steps:**
```powershell
# 1. Clone and push to GitHub (if not already done)
git clone https://github.com/arun3676/ai-learning-path-generator.git
cd ai-learning-path-generator

# 2. Create Redis instance
# Go to https://redis.com/try-free/
# Create database, copy connection string

# 3. Deploy Backend API
# Go to https://dashboard.render.com/
# New → Web Service
# Root Directory: backend
# Build: pip install -r requirements.txt
# Add env vars:
#   REDIS_URL=redis://...
#   OPENAI_API_KEY=sk-...

# 4. Deploy Worker
# New → Background Worker
# Root Directory: worker
# Same env vars as backend

# 5. Test API
Invoke-RestMethod https://your-api.onrender.com/health
```

**Detailed Guide:** `HYBRID_DEPLOYMENT_GUIDE.md`

### 2. React Frontend (5 minutes)

**Prerequisites:**
- Vercel account (free)
- Backend API deployed

**Steps:**
```powershell
# 1. Deploy to Vercel
# Go to https://vercel.com/new
# Import your GitHub repo
# Configure:
#   Framework: Vite
#   Root Directory: frontend
#   Env var: VITE_API_URL=https://your-api.onrender.com

# 2. Deploy!
# Click "Deploy"
# Wait 1-2 minutes
# Done! ✅
```

**Detailed Guide:** `PHASE2_DEPLOYMENT_GUIDE.md`

## 🧪 Local Development

### Backend + Worker (Using Docker)

```powershell
# 1. Create .env file
Copy-Item .env.example .env
# Edit .env with your API keys

# 2. Start all services
docker-compose -f docker-compose.dev.yml up

# Backend API: http://localhost:5000
# Redis: localhost:6379
# Worker: Running in background
```

### Frontend Only

```powershell
# 1. Install dependencies
cd frontend
npm install

# 2. Configure API
Copy-Item .env.example .env
# Edit: VITE_API_URL=http://localhost:5000

# 3. Start dev server
npm run dev

# Open: http://localhost:3000
```

**Or use automated setup:**
```powershell
cd frontend
.\setup.ps1
```

## 🎨 Test the Complete Flow

### 1. Open Frontend
Go to your Vercel URL or `http://localhost:3000`

### 2. Fill Form
- **Topic:** "Python Data Analysis"
- **Level:** Beginner
- **Duration:** 4 weeks
- **Commitment:** Moderate
- **Goals:** "Become productive with pandas"

### 3. Watch Progress
- See real-time updates
- Progress bar shows completion
- Status messages update

### 4. View Results
- Overview statistics
- Job market insights
- Expandable milestones
- Learning resources
- Export to JSON

## 📊 Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                    USER FLOW                         │
└──────────────────────────────────────────────────────┘

User → Vercel Frontend (React)
           ↓
    POST /api/generate
           ↓
    Render Backend (Flask) → Redis Queue
           ↓                      ↓
    Returns task_id        Worker picks up
           ↓                      ↓
    Poll /status          Generates path
           ↓                      ↓
    GET /result      ← Stores in Redis
           ↓
    Display to user
```

## 💰 Cost Breakdown

| Service | Plan | Cost |
|---------|------|------|
| **Vercel Frontend** | Hobby | FREE |
| **Render Backend API** | Starter | $7/month |
| **Render Worker** | Starter | $7/month |
| **Redis Cloud** | Free | FREE |
| **Total** | | **$14/month** |

## 📚 Documentation Quick Reference

| Need | Document |
|------|----------|
| Deploy backend | `HYBRID_DEPLOYMENT_GUIDE.md` |
| Deploy frontend | `PHASE2_DEPLOYMENT_GUIDE.md` |
| Backend overview | `PHASE1_README.md` |
| Frontend overview | `PHASE2_README.md` |
| Complete summary | `PHASE2_COMPLETE.md` |
| API reference | `backend/routes.py` |
| Frontend components | `frontend/README.md` |

## 🐛 Troubleshooting

### Backend Issues

**Worker not processing tasks:**
```powershell
# Check Render worker logs
# Verify Redis connection
# Check OPENAI_API_KEY is set
```

**API returns 500:**
```powershell
# Check Render API logs
# Verify all env vars set
# Test Redis connection
```

### Frontend Issues

**Blank page:**
```powershell
# Check browser console for errors
# Verify VITE_API_URL in Vercel
# Check API is accessible
```

**CORS errors:**
```python
# Update backend/app.py:
CORS(app, origins=["https://your-app.vercel.app"])
```

**Progress stuck:**
```powershell
# Check worker is running on Render
# Verify Redis connection
# Check worker logs
```

## ✅ Success Checklist

- [ ] Backend API deployed on Render
- [ ] Worker deployed on Render
- [ ] Redis connected to both
- [ ] Frontend deployed on Vercel
- [ ] Frontend connected to API
- [ ] Test path generation works
- [ ] Progress updates in real-time
- [ ] Results display correctly
- [ ] Mobile responsive
- [ ] No console errors

## 🎉 Next Steps

Once everything is working:

1. **Share your app** - Send Vercel URL to friends
2. **Monitor usage** - Check Render & Vercel dashboards
3. **Optimize costs** - Adjust workers as needed
4. **Add features** - See Phase 3 ideas in `PHASE2_README.md`
5. **Get feedback** - Improve based on user input

## 🆘 Need Help?

1. Check documentation in root directory
2. Review logs in Render/Vercel dashboards
3. Test API endpoints directly with curl/Postman
4. Check browser console for frontend errors
5. Verify all environment variables are set

---

**Congratulations!** You now have a production-ready AI application! 🚀
