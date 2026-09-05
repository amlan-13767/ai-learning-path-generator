# Render Environment Variables - Quick Reference

Copy and paste these into your Render dashboard under **Environment** tab.

## ✅ REQUIRED Variables

```
OPENAI_API_KEY=your_actual_openai_key_here
FLASK_SECRET_KEY=generate_a_strong_random_key_here
FLASK_ENV=production
FLASK_APP=run.py
DEBUG=False
```

## 🔧 Optional but Recommended

### Perplexity (for resource search)
```
PERPLEXITY_API_KEY=your_perplexity_key_here
```

### Google OAuth (for user authentication)
```
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
```

## 📊 Observability (Optional)

### LangSmith (LLM tracing)
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=ai-learning-path-generator
```

### Weights & Biases (metrics tracking)
```
WANDB_API_KEY=your_wandb_key
WANDB_PROJECT=ai-learning-path-generator
WANDB_ENTITY=your_wandb_username
```

## 🗄️ Database & Cache

### Redis (automatically set by Render add-on)
```
REDIS_URL=automatically_set_by_render
```

### PostgreSQL (automatically set by Render add-on)
```
DATABASE_URL=automatically_set_by_render
```

## 🎨 Model Configuration (Optional)

```
DEFAULT_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-ada-002
```

---

## 🔐 How to Generate a Strong Secret Key

Run this in Python:

```python
import secrets
print(secrets.token_urlsafe(32))
```

Or use this command:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 📝 Notes

1. **Never commit these values to GitHub**
2. **Redis and Database URLs** are automatically set when you add the add-ons
3. **Start with required variables**, add optional ones as needed
4. **Update Google OAuth redirect URIs** after deployment
5. **Test locally first** with your `.env` file before deploying

---

## ✨ Minimal Setup (Just to Get Started)

If you want to deploy quickly with minimal configuration:

```
OPENAI_API_KEY=your_actual_openai_key_here
FLASK_SECRET_KEY=your_generated_secret_key
FLASK_ENV=production
FLASK_APP=run.py
DEBUG=False
REDIS_URL=automatically_set_by_render_addon
```

Add Redis add-on, and you're good to go! 🚀
