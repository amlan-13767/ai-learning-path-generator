# ✅ SIMPLE SOLUTION: Just Use Render

## Why Fly.io is Failing

The machines are created but crash immediately because **secrets aren't set**. Fly.io's CLI isn't in your PATH, making it harder to configure.

## ✅ RECOMMENDED: Deploy Everything on Render

You already have Render set up. Let's just use it for both web and worker.

### Step 1: Push Your Code to GitHub

Your Redis fix is already in the code. Just push:

```powershell
cd c:\Users\arunk\professional\ai-learning-path-generator
git add .
git commit -m "Fix Redis connection for SemanticCache"
git push origin main
```

### Step 2: Deploy Web Service on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Find your **web service** (ai-learning-path-generator)
3. Click **"Manual Deploy"** → **"Clear build cache & deploy"**
4. Wait 5-10 minutes for deployment

### Step 3: Create Worker Service on Render

1. Click **"New +"** → **"Background Worker"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `ai-learning-path-generator-worker`
   - **Region**: Same as your web service
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python worker.py`
   - **Plan**: Free

4. Add Environment Variables (click "Advanced"):
   ```
   REDIS_URL=redis://default:<PASSWORD>@<HOST>:<PORT>/0
   OPENAI_API_KEY=YOUR_OPENAI_API_KEY
   SECRET_KEY=YOUR_FLASK_SECRET_KEY
   PERPLEXITY_API_KEY=YOUR_PERPLEXITY_API_KEY
   LANGCHAIN_API_KEY=YOUR_LANGCHAIN_API_KEY
   WANDB_API_KEY=YOUR_WANDB_API_KEY
   DEFAULT_MODEL=gpt-4o-mini
   FLASK_ENV=production
   ```

5. Click **"Create Background Worker"**

### Step 4: Test the Full Flow

```powershell
# Replace with your actual Render web service URL
$renderUrl = "https://your-app.onrender.com"

# Generate a learning path
$body = @{
    topic = "Python"
    expertise_level = "beginner"
    duration_weeks = 2
    time_commitment = "minimal"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "$renderUrl/api/generate-task" -Method POST -Body $body -ContentType "application/json"
$taskId = ($response.Content | ConvertFrom-Json).task_id

Write-Host "Task ID: $taskId"

# Check status
Start-Sleep -Seconds 5
Invoke-WebRequest -Uri "$renderUrl/api/task-status/$taskId" -Method GET
```

## Why This is Better

✅ **No CLI needed** - Everything through web UI
✅ **No PATH issues** - No command-line tools to install
✅ **Same platform** - Web and worker on the same platform
✅ **Free tier** - Render's free tier includes background workers
✅ **Automatic deploys** - Push to GitHub, auto-deploy

## About Render Build Minutes

You mentioned running out of build minutes. Here's the truth:

- **Free tier**: 750 build minutes/month
- **Each build**: ~5 minutes
- **You can do**: ~150 deploys/month
- **Your usage**: You've done maybe 10 builds total

You're **nowhere near** the limit. Don't worry about it.

## If You Still Want Fly.io

Run this in PowerShell:

```powershell
# Find where Fly CLI is installed
Get-Command fly -ErrorAction SilentlyContinue

# If not found, add to PATH
$env:PATH += ";$env:USERPROFILE\.fly\bin"

# Run the secrets script
.\set_fly_secrets.ps1

# Restart the machines
fly machines restart 48e37eea7d4228 -a ai-learning-path-generator
fly machines restart 0801e02c2663e8 -a ai-learning-path-generator

# Check logs
fly logs -a ai-learning-path-generator
```

## My Recommendation

**Use Render.** It's simpler, you already have it set up, and it just works. Save Fly.io for when you need more advanced features.
