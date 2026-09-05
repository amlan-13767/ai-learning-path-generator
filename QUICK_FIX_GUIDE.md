# 🔧 Quick Fix Guide - Common Issues

## ✅ Issue Fixed: Model Name Error

### **Problem:**
```
Error code: 404 - The model `GPT-4o-mini` does not exist
```

### **Cause:**
Model name was uppercase `GPT-4o-mini` instead of lowercase `gpt-4o-mini`

### **Fix Applied:**
Changed `.env` file:
```
# Before
DEFAULT_MODEL=GPT-4o-mini

# After
DEFAULT_MODEL=gpt-4o-mini
```

---

## 🚀 Restart Flask to Apply Fix

**Important:** You need to restart Flask for the .env changes to take effect.

```powershell
# 1. Stop Flask (press Ctrl+C in the terminal where it's running)

# 2. Restart Flask
python run_flask.py
```

---

## ✅ Valid OpenAI Model Names

Use these exact names (case-sensitive):

### **Recommended (Cheap & Fast):**
- `gpt-4o-mini` - Best value! $0.15/1M tokens
- `gpt-3.5-turbo` - Classic, $0.50/1M tokens

### **Advanced (More Expensive):**
- `gpt-4o` - Latest GPT-4, $2.50/1M tokens
- `gpt-4-turbo` - Fast GPT-4, $10/1M tokens
- `gpt-4` - Original GPT-4, $30/1M tokens

### **Embeddings:**
- `text-embedding-3-small` - Cheap, $0.02/1M tokens
- `text-embedding-ada-002` - Classic, $0.10/1M tokens

---

## 🔍 How to Verify Your .env File

```powershell
# Check current model setting
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'Model: {os.getenv(\"DEFAULT_MODEL\")}')"
```

**Expected output:**
```
Model: gpt-4o-mini
```

---

## 📝 Complete .env Template

```env
# OpenAI API Key (REQUIRED)
OPENAI_API_KEY=sk-proj-your-key-here

# Flask Configuration
FLASK_APP=run_flask.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-in-production

# Database
DATABASE_URL=sqlite:///learning_path.db

# AI Model Configuration (all lowercase!)
DEFAULT_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
MAX_TOKENS=1000
TEMPERATURE=0.7

# Optional
DEV_MODE=False
DEFAULT_PROVIDER=openai
```

---

## 🐛 Other Common Errors

### **Error: "API key not found"**
**Fix:** Check your `.env` file has `OPENAI_API_KEY=sk-...`

### **Error: "Rate limit exceeded"**
**Fix:** You've hit OpenAI's rate limit. Wait a few minutes or upgrade your OpenAI plan.

### **Error: "Insufficient quota"**
**Fix:** Add credits to your OpenAI account at https://platform.openai.com/account/billing

### **Error: "Invalid API key"**
**Fix:** Generate a new API key at https://platform.openai.com/api-keys

---

## ✅ Verification Steps

After restarting Flask:

1. **Check Flask starts without errors**
   ```
   ✅ Should see: "Running on http://127.0.0.1:5000"
   ```

2. **Test learning path generation**
   - Go to http://localhost:5000/generate
   - Fill in the form
   - Click "Generate Learning Path"
   - ✅ Should generate successfully

3. **Check browser console (F12)**
   - ✅ No red errors

---

## 🎯 Summary

**What was fixed:**
- ✅ Changed `DEFAULT_MODEL=GPT-4o-mini` to `DEFAULT_MODEL=gpt-4o-mini` in `.env`

**What you need to do:**
1. Restart Flask (Ctrl+C, then `python run_flask.py`)
2. Test the application
3. Should work now! 🎉

---

*Quick fix guide for AI Learning Path Generator*
*Last updated: 2025-09-30*
