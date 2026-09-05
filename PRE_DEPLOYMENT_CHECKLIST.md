# Pre-Deployment Checklist

Use this checklist before pushing to GitHub and deploying to Render.

## Status: READY FOR DEPLOYMENT

### Phase 1 Complete - All Systems Go!
- [ ] `requirements.txt` is complete and up-to-date
- [ ] `Procfile` exists and is correct
- [ ] `.gitignore` includes all sensitive files
- [ ] `README.md` is updated with deployment instructions

### Test Locally:
- [ ] App runs without errors: `python run.py`
- [ ] All features work (generate learning path, caching, etc.)
- [ ] Redis connection works (if using Docker)
- [ ] No hardcoded API keys in the code
- [ ] All environment variables are loaded from `.env`

### Git Commands:
```bash
# Check what will be committed
git status

# Make sure .env is NOT in the list!
# If it is, add it to .gitignore immediately

# Add all changes
git add .

# Commit
git commit -m "Prepare for Render deployment"

# Push to GitHub
git push origin main
```

## 🔑 API Keys Ready

Have these ready before deploying:

### Required:
- [ ] OpenAI API Key
- [ ] Flask Secret Key (generate a new one for production)

### Optional:
- [ ] Perplexity API Key
- [ ] Google OAuth Client ID & Secret
- [ ] LangSmith API Key
- [ ] Weights & Biases API Key

## 🚀 Render Setup

### Before Creating Web Service:
- [ ] GitHub repository is public or connected to Render
- [ ] Repository has all necessary files
- [ ] No sensitive data in repository

### During Web Service Creation:
- [ ] Correct repository selected
- [ ] Correct branch selected (usually `main`)
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
- [ ] Instance type selected (Free or Starter)

### Environment Variables:
- [ ] All required variables added
- [ ] Secret key is strong and unique
- [ ] API keys are correct (no extra spaces!)
- [ ] `DEBUG=False` for production
- [ ] `FLASK_ENV=production`

### Add-ons:
- [ ] Redis add-on created and connected
- [ ] PostgreSQL add-on created (if needed)
- [ ] `REDIS_URL` automatically set
- [ ] `DATABASE_URL` automatically set (if using PostgreSQL)

## ✅ Post-Deployment Verification

### After First Deploy:
- [ ] App builds successfully (check logs)
- [ ] App starts without errors (check logs)
- [ ] Homepage loads correctly
- [ ] Can generate a learning path
- [ ] Redis caching works (test by generating same path twice)
- [ ] No errors in Render logs

### Google OAuth (if configured):
- [ ] Redirect URIs updated in Google Cloud Console
- [ ] OAuth login works
- [ ] User can authenticate successfully

### Performance:
- [ ] App responds quickly
- [ ] No timeout errors
- [ ] Memory usage is reasonable
- [ ] CPU usage is reasonable

## 🔒 Security Check

- [ ] `.env` file is NOT in GitHub
- [ ] All API keys are in environment variables
- [ ] No hardcoded secrets in code
- [ ] HTTPS is enabled (Render provides this automatically)
- [ ] Session cookies are secure
- [ ] CORS is configured properly (if needed)

## 📊 Monitoring Setup

- [ ] Can access Render logs
- [ ] Can view metrics (CPU, Memory, Requests)
- [ ] Email alerts configured (optional)
- [ ] LangSmith tracing works (if configured)
- [ ] Weights & Biases tracking works (if configured)

## 🐛 Troubleshooting Prepared

- [ ] Know how to view logs in Render
- [ ] Know how to restart the service
- [ ] Know how to rollback to previous version
- [ ] Have local backup of working code
- [ ] Can test locally if issues arise

## 📝 Documentation

- [ ] `RENDER_DEPLOYMENT_GUIDE.md` is available
- [ ] `RENDER_ENV_VARIABLES.md` is available
- [ ] `README.md` has deployment section
- [ ] Team members know how to access Render dashboard

## 🎯 Final Steps

1. **Review this entire checklist** ✅
2. **Test everything locally** ✅
3. **Commit and push to GitHub** ✅
4. **Create Render Web Service** ✅
5. **Add environment variables** ✅
6. **Add Redis add-on** ✅
7. **Deploy and verify** ✅
8. **Monitor for 24 hours** ✅

---

## 🚨 Common Mistakes to Avoid

1. ❌ Committing `.env` file to GitHub
2. ❌ Forgetting to add Redis add-on
3. ❌ Using weak secret keys
4. ❌ Not setting `DEBUG=False` in production
5. ❌ Forgetting to update Google OAuth redirect URIs
6. ❌ Not testing locally before deploying
7. ❌ Ignoring error logs after deployment
8. ❌ Not having a rollback plan

---

## ✨ You're Ready!

If all items are checked, you're ready to deploy! 🚀

**Good luck with your deployment!** 🎉
