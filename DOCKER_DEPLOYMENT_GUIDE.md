# Docker Deployment Guide

This guide explains how Docker works and how to deploy your AI Learning Path Generator using Docker on Fly.io.

## What is Docker?

Docker is a tool that packages your application and all its dependencies into a "container" - think of it as a lightweight, portable box that contains everything your app needs to run.

### Key Concepts:

1. **Dockerfile**: A recipe that tells Docker how to build your application's container
2. **Image**: The built container (like a snapshot of your app ready to run)
3. **Container**: A running instance of an image (your app actually executing)

### Why Use Docker?

- **Consistency**: Your app runs the same way everywhere (your laptop, Render, Fly.io, etc.)
- **Fast Deployments**: After the first build, subsequent deployments are very fast
- **Efficiency**: Only rebuilds what changed (e.g., if you change code but not dependencies, it only copies the new code)
- **Cost Savings**: Dramatically reduces build time, saving you money on platforms that charge for build minutes

## Understanding the Dockerfile

Let's break down the `Dockerfile` I created for you:

```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.11-slim
```
- **What it does**: Starts with a pre-built Python 3.11 environment
- **Why slim**: The "slim" version is smaller and faster to download

```dockerfile
# Set the working directory in the container
WORKDIR /app
```
- **What it does**: Creates a folder called `/app` inside the container and makes it the current directory
- **Why**: Keeps everything organized

```dockerfile
# Install system dependencies required for some Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*
```
- **What it does**: Installs C/C++ compilers needed by some Python packages (like numpy, scipy)
- **Why**: Some Python packages need to compile C code during installation

```dockerfile
# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
```
- **What it does**: Copies your `requirements.txt` and installs all Python packages
- **Why this is CRITICAL**: Docker caches this step. If `requirements.txt` doesn't change, Docker reuses the cached layer, making builds 10x faster!

```dockerfile
# Copy the rest of your application code into the container
COPY . .
```
- **What it does**: Copies all your Python code into the container
- **Why it's separate**: By copying code AFTER installing dependencies, code changes don't trigger a full dependency reinstall

```dockerfile
# Create necessary directories
RUN mkdir -p vector_db cache learning_paths
```
- **What it does**: Creates folders your app needs at runtime

```dockerfile
# Expose the port the app runs on
EXPOSE 5000
```
- **What it does**: Documents that your app listens on port 5000
- **Note**: This is just documentation; the actual port is set by the start command

```dockerfile
# Default command
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120"]
```
- **What it does**: Defines the default command to run when the container starts
- **Note**: Fly.io and Render will override this with their own start commands

## How to Deploy the Worker to Fly.io

### Step 1: Install Fly.io CLI

Open PowerShell and run:
```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

After installation, close and reopen PowerShell.

### Step 2: Sign Up and Log In

```powershell
fly auth signup
fly auth login
```

### Step 3: Navigate to Your Project

```powershell
cd c:\Users\arunk\professional\ai-learning-path-generator
```

### Step 4: Launch Your Worker App

```powershell
fly launch
```

You'll be asked several questions:
- **App name**: Choose something like `arun-ai-worker` (must be globally unique)
- **Region**: Choose the closest region (e.g., `iad` for US East)
- **Postgres database**: Say **No**
- **Redis**: Say **No** (you're using Upstash)
- **Deploy now**: Say **No**

### Step 5: Configure the Worker

A file called `fly.toml` was created. Open it and replace its contents with:

```toml
app = "arun-ai-worker"  # Use the app name you chose
primary_region = "iad"  # Use the region you chose

[build]
  dockerfile = "Dockerfile"

# This tells Fly.io to run as a background worker, not a web server
[processes]
  worker = "python worker.py"

[[services]]
  # No services block needed for a worker (it doesn't accept HTTP traffic)
```

### Step 6: Set Environment Variables (Secrets)

Run these commands one by one, replacing the values with your actual keys:

```powershell
fly secrets set OPENAI_API_KEY="sk-proj-..."
fly secrets set REDIS_URL="rediss://default:YOUR_PASSWORD@diverse-cricket-21376.upstash.io:6379"
fly secrets set FLASK_SECRET_KEY="any-random-string-here"
```

If you use Perplexity:
```powershell
fly secrets set PERPLEXITY_API_KEY="your-perplexity-key"
```

### Step 7: Deploy

```powershell
fly deploy
```

This will:
1. Build your Docker image (takes 2-3 minutes the first time)
2. Upload it to Fly.io
3. Start your worker

### Step 8: Monitor Your Worker

To see if it's running:
```powershell
fly logs
```

You should see:
```
Starting RQ worker, listening on queues: learning-paths...
*** Listening on learning-paths...
```

## How the System Works Together

```
┌─────────────────┐
│   User Browser  │
└────────┬────────┘
         │ HTTP Request
         ▼
┌─────────────────┐
│  Render Web     │ ← Handles web requests
│  Service        │ ← Enqueues jobs to Redis
└────────┬────────┘
         │
         │ Job: "Generate path for Machine Learning"
         ▼
┌─────────────────┐
│  Upstash Redis  │ ← Message queue (the "glue")
│  Database       │ ← Stores pending jobs
└────────┬────────┘
         │
         │ Worker polls for jobs
         ▼
┌─────────────────┐
│  Fly.io Worker  │ ← Picks up jobs
│  Service        │ ← Generates learning paths
└────────┬────────┘
         │
         │ Stores result back in Redis
         ▼
┌─────────────────┐
│  Upstash Redis  │
└────────┬────────┘
         │
         │ Web service retrieves result
         ▼
┌─────────────────┐
│  User Browser   │ ← Sees the generated path
└─────────────────┘
```

## Testing the System

After deploying the worker to Fly.io, test the full flow:

```powershell
$body = @{
  topic = "Machine Learning"
  expertise_level = "intermediate"
  duration_weeks = 4
  time_commitment = "moderate"
} | ConvertTo-Json

try {
  $response = Invoke-WebRequest `
    -Uri "https://ai-learning-path-api.onrender.com/api/generate-task" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
  
  $json = $response.Content | ConvertFrom-Json
  $taskId = $json.task_id
  Write-Host "✅ Task created: $taskId"
  
  # Poll for status
  Start-Sleep -Seconds 5
  $status = Invoke-WebRequest `
    -Uri "https://ai-learning-path-api.onrender.com/api/task-status/$taskId" `
    | Select-Object -ExpandProperty Content
  
  Write-Host "Status: $status"
} catch {
  $_.Exception.Response.GetResponseStream() | % { 
    New-Object IO.StreamReader($_) 
  } | % { 
    $_.ReadToEnd() 
  }
}
```

## Troubleshooting

### Worker Not Picking Up Jobs

**Check Fly.io logs:**
```powershell
fly logs
```

**Verify Redis URL is correct:**
```powershell
fly secrets list
```

### Web Service Can't Connect to Redis

The fix I applied should resolve this. After you push the code changes to GitHub, trigger a manual deploy on Render (you still have the web service running).

### Build Takes Too Long

This is normal for the first Docker build. Subsequent builds will be much faster because Docker caches the dependency installation layer.

## Cost Optimization

- **Fly.io Free Tier**: 3 shared-cpu-1x VMs with 256MB RAM each (perfect for a worker)
- **Render Free Tier**: You've used it up, but with Docker, future builds will be much cheaper
- **Upstash Free Tier**: 10,000 commands/day (plenty for testing)

## Next Steps

1. **Push the code fix to GitHub** (the SemanticCache Redis URL fix)
2. **Deploy the worker to Fly.io** (follow steps above)
3. **Test the full flow** using the PowerShell script
4. **Optional**: Move the web service to Fly.io too if you want to consolidate platforms

## Summary

Docker solves your deployment cost problem by:
1. Building once, deploying many times
2. Caching dependencies so only code changes trigger rebuilds
3. Making deployments fast (30 seconds instead of 5 minutes)

The hybrid setup (Render Web + Fly.io Worker) gives you:
1. Two free tiers to work with
2. A working system while you learn Docker
3. The flexibility to move everything to one platform later
