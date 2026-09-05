# Render Deployment Guide

This guide will walk you through deploying your AI Learning Path Generator to Render.

## Prerequisites

1. **GitHub Account**: Your code must be in a GitHub repository
2. **Render Account**: Sign up at [render.com](https://render.com)
3. **API Keys**: Have all your API keys ready (OpenAI, Perplexity, etc.)

## Step 1: Prepare Your Repository

### 1.1 Ensure `.env` is NOT committed
```bash
# Check if .env is in .gitignore
cat .gitignore | grep .env
```

### 1.2 Commit and push your code to GitHub
```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

## Step 2: Create a Web Service on Render

1. **Log in to Render Dashboard**: https://dashboard.render.com
2. **Click "New +"** → Select **"Web Service"**
3. **Connect Your Repository**:
   - Click "Connect account" to link your GitHub
   - Select your repository: `ai-learning-path-generator`
   - Click "Connect"

## Step 3: Configure Your Web Service

### Basic Settings:
- **Name**: `ai-learning-path-generator` (or your preferred name)
- **Region**: Choose closest to your users (e.g., Oregon, Frankfurt)
- **Branch**: `main` (or your default branch)
- **Root Directory**: Leave empty
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

### Instance Type:
- **Free Tier**: Good for testing (spins down after inactivity)
- **Starter ($7/month)**: Recommended for production (always on)

## Step 4: Add Environment Variables

Click on **"Environment"** tab and add these variables:

### Required API Keys:
```
OPENAI_API_KEY=your_actual_openai_key
PERPLEXITY_API_KEY=your_actual_perplexity_key
```

### Flask Configuration:
```
FLASK_APP=run.py
FLASK_ENV=production
FLASK_SECRET_KEY=generate_a_strong_random_key_here
DEBUG=False
```

### Google OAuth (if using):
```
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
```

### Optional - Observability:
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=ai-learning-path-generator

WANDB_API_KEY=your_wandb_key
WANDB_PROJECT=ai-learning-path-generator
```

## Step 5: Add Redis Add-on

1. In your Web Service dashboard, scroll to **"Add-ons"**
2. Click **"Add Redis"**
3. Choose a plan:
   - **Free**: 25MB storage (good for testing)
   - **Starter ($7/month)**: 256MB storage (recommended)
4. Click **"Create Redis"**
5. The `REDIS_URL` environment variable will be automatically added

## Step 6: Add PostgreSQL Database (Optional)

If you want to use PostgreSQL instead of SQLite:

1. In your dashboard, click **"New +"** → **"PostgreSQL"**
2. Choose a plan:
   - **Free**: 90-day expiration (good for testing)
   - **Starter ($7/month)**: Persistent database
3. Click **"Create Database"**
4. Copy the **Internal Database URL**
5. Add it to your Web Service environment variables:
   ```
   DATABASE_URL=your_postgresql_internal_url
   ```

## Step 7: Deploy

1. Click **"Create Web Service"** at the bottom
2. Render will start building and deploying your app
3. Watch the logs for any errors
4. Once deployed, you'll get a URL like: `https://ai-learning-path-generator.onrender.com`

## Step 8: Verify Deployment

1. **Visit your app URL**
2. **Test the following**:
   - Homepage loads correctly
   - Generate a learning path
   - Check if Redis caching works (generate same path twice)
   - Test Google OAuth login (if configured)

## Step 9: Configure Google OAuth Redirect URIs

If using Google OAuth, update your Google Cloud Console:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **APIs & Services** → **Credentials**
3. Click on your OAuth 2.0 Client ID
4. Add these to **Authorized redirect URIs**:
   ```
   https://your-app-name.onrender.com/login/google/authorized
   https://your-app-name.onrender.com/oauth2callback
   ```
5. Save changes

## Troubleshooting

### Build Fails
- Check the build logs in Render dashboard
- Ensure `requirements.txt` is correct
- Verify Python version compatibility

### App Crashes on Start
- Check the logs for error messages
- Ensure all required environment variables are set
- Verify `OPENAI_API_KEY` is set correctly

### Redis Connection Fails
- Ensure Redis add-on is created and connected
- Check if `REDIS_URL` environment variable exists
- Verify your code handles Redis connection errors gracefully

### Database Issues
- If using PostgreSQL, ensure `DATABASE_URL` is set
- Check database connection in logs
- Verify migrations have run (if applicable)

## Cost Summary

### Minimum Setup (Free Tier):
- Web Service: Free (spins down after inactivity)
- Redis: Free (25MB)
- PostgreSQL: Free (90-day expiration)
- **Total: $0/month**

### Recommended Production Setup:
- Web Service: $7/month (Starter - always on)
- Redis: $7/month (256MB)
- PostgreSQL: $7/month (persistent)
- **Total: $21/month**

### Budget-Friendly Production:
- Web Service: $7/month (Starter)
- Redis: Free (25MB - sufficient for most use cases)
- Database: SQLite (included, no extra cost)
- **Total: $7/month**

## Monitoring Your App

### View Logs:
1. Go to your Web Service dashboard
2. Click on **"Logs"** tab
3. Monitor real-time logs

### Metrics:
1. Click on **"Metrics"** tab
2. View CPU, Memory, and Request metrics

### Alerts:
1. Set up email alerts for deployment failures
2. Configure health checks

## Updating Your App

Render automatically deploys when you push to your connected branch:

```bash
# Make changes to your code
git add .
git commit -m "Update feature X"
git push origin main
```

Render will automatically:
1. Detect the push
2. Build your app
3. Deploy the new version
4. Zero-downtime deployment (on paid plans)

## Environment Variables Management

### To update environment variables:
1. Go to your Web Service dashboard
2. Click **"Environment"** tab
3. Add/Edit/Delete variables
4. Click **"Save Changes"**
5. Render will automatically redeploy

## Backup Strategy

### Database Backups:
- PostgreSQL on Render has automatic daily backups
- SQLite: Not recommended for production

### Code Backups:
- Your code is in GitHub (version controlled)
- Render pulls from GitHub on each deploy

## Security Best Practices

1. **Never commit `.env` file** to GitHub
2. **Use strong secret keys** for Flask
3. **Enable HTTPS** (Render provides free SSL)
4. **Rotate API keys** regularly
5. **Monitor logs** for suspicious activity
6. **Use environment variables** for all secrets

## Support

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com
- **Your App Logs**: Check Render dashboard for detailed logs

## Next Steps

1. ✅ Deploy to Render
2. ✅ Test all features
3. ✅ Set up monitoring
4. ✅ Configure custom domain (optional)
5. ✅ Set up CI/CD (automatic with GitHub integration)

---

**Congratulations!** Your AI Learning Path Generator is now live on Render! 🎉
