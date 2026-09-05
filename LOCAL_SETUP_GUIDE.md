# 🚀 Local Setup & Testing Guide

## Prerequisites
- Python 3.11 installed
- OpenAI API key (get from https://platform.openai.com/api-keys)
- Git installed

---

## Step 1: Install Dependencies

### Clean Install (Recommended)
```powershell
# Navigate to project directory
cd c:\Users\arunk\professional\ai-learning-path-generator

# Create virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

### If You Get Errors
```powershell
# Clear pip cache
pip cache purge

# Uninstall problematic packages
pip uninstall -y pydantic pydantic-core pydantic-settings

# Reinstall with no cache
pip install --no-cache-dir "pydantic[email]==1.10.18"

# Install remaining packages
pip install -r requirements.txt
```

---

## Step 2: Configure Environment Variables

### Create .env file (if not exists)
```powershell
# Check if .env exists
if (!(Test-Path .env)) {
    New-Item -Path .env -ItemType File
}

# Open .env in notepad
notepad .env
```

### Add these variables to .env:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Flask Configuration
FLASK_APP=run_flask.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-change-in-production

# Database Configuration
DATABASE_URL=sqlite:///learning_path.db

# Optional: DeepSeek (if you want to use it)
DEEPSEEK_API_KEY=your_deepseek_key_here

# Development Mode (set to False for production)
DEV_MODE=False
```

---

## Step 3: Initialize Database

```powershell
# Run database migration
python -m migrations.add_chatbot_tables
```

### If migration fails:
```powershell
# Check if database exists
if (Test-Path learning_path.db) {
    Write-Host "Database exists"
} else {
    Write-Host "Database will be created on first run"
}
```

---

## Step 4: Run the Application

### Start Flask Server
```powershell
# Method 1: Using run_flask.py
python run_flask.py

# Method 2: Using Flask CLI
flask run

# Method 3: With specific host/port
python run_flask.py --host 0.0.0.0 --port 5000
```

### Expected Output:
```
--- Successfully loaded .env from: C:\Users\arunk\...
 * Serving Flask app 'web_app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in production.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

---

## Step 5: Test the Application

### Open in Browser
```
http://localhost:5000
```

### Test Endpoints

#### 1. Home Page
```
http://localhost:5000/
```

#### 2. Generate Learning Path (if logged in)
```
http://localhost:5000/generate
```

#### 3. Chatbot (if logged in)
```
http://localhost:5000/chatbot
```

---

## Step 6: Test Few-Shot Prompting Feature

### Using Python Shell
```powershell
python
```

```python
from src.learning_path import LearningPathGenerator

# Initialize generator
generator = LearningPathGenerator()

# Test 1: Generate Python path
path = generator.generate_path(
    topic="Python Programming",
    expertise_level="beginner",
    learning_style="visual",
    time_commitment="moderate",
    goals=["Master Python basics", "Build projects"]
)

print(f"Title: {path.title}")
print(f"Milestones: {len(path.milestones)}")
print(f"Total Hours: {path.total_hours}")

# Test 2: Generate different topic
path2 = generator.generate_path(
    topic="Machine Learning",
    expertise_level="intermediate",
    learning_style="hands-on",
    time_commitment="substantial"
)

print(f"\nTitle: {path2.title}")
print(f"Milestones: {len(path2.milestones)}")
```

---

## Troubleshooting

### Issue 1: Pydantic Version Conflicts
```powershell
pip uninstall -y pydantic pydantic-core pydantic-settings
pip install --no-cache-dir "pydantic[email]==1.10.18"
```

### Issue 2: LangChain Import Errors
```powershell
pip uninstall -y langchain langchain-core langchain-openai langchain-community
pip install langchain==0.0.354 "langchain-openai<0.1" "langchain-community<0.1"
```

### Issue 3: Database Errors
```powershell
# Delete and recreate database
Remove-Item learning_path.db -ErrorAction SilentlyContinue
python -m migrations.add_chatbot_tables
```

### Issue 4: Port Already in Use
```powershell
# Find process using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or use different port
python run_flask.py --port 5001
```

### Issue 5: OpenAI API Key Not Found
```powershell
# Check if .env is loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"
```

---

## Verification Checklist

- [ ] Dependencies installed successfully
- [ ] .env file configured with API keys
- [ ] Database initialized
- [ ] Flask server starts without errors
- [ ] Can access http://localhost:5000
- [ ] Few-shot prompting works in Python shell
- [ ] No Pydantic version conflicts

---

## Production Deployment

### Before Pushing to GitHub:
```powershell
# 1. Ensure .env is in .gitignore
echo ".env" >> .gitignore

# 2. Update requirements.txt if needed
pip freeze > requirements.txt

# 3. Run tests
pytest

# 4. Commit changes
git add .
git commit -m "Add few-shot prompting feature"
git push origin main
```

### Deploy to Render/Heroku:
1. Set environment variables in platform dashboard
2. Set `DEV_MODE=False`
3. Use PostgreSQL for production database
4. Configure `DATABASE_URL` to PostgreSQL connection string

---

## Quick Commands Summary

```powershell
# Install
pip install -r requirements.txt

# Configure
notepad .env  # Add OPENAI_API_KEY

# Initialize DB
python -m migrations.add_chatbot_tables

# Run
python run_flask.py

# Test
python -c "from src.learning_path import LearningPathGenerator; g = LearningPathGenerator(); print('✅ Setup successful!')"
```

---

## Next Steps After Local Testing

1. ✅ Test all features locally
2. ✅ Verify few-shot prompting works
3. ✅ Check database operations
4. ✅ Test chatbot functionality
5. 🚀 Push to GitHub
6. 🚀 Deploy to production

---

*Setup guide for AI Learning Path Generator*
*Last updated: 2025-09-30*
