# 🔐 Google OAuth Setup & Troubleshooting

**Date**: 2025-10-04  
**Status**: Configuration Required

---

## The 400 Error Explained

The **"400. That's an error. The server cannot process the request because it is malformed"** error from Google OAuth typically means:

1. **Redirect URI Mismatch**: The redirect URI in your code doesn't match what's configured in Google Cloud Console
2. **Missing/Invalid Credentials**: `GOOGLE_OAUTH_CLIENT_ID` or `GOOGLE_OAUTH_CLIENT_SECRET` are incorrect
3. **OAuth Consent Screen Not Configured**: Google Cloud project needs proper setup

---

## ✅ Fix Applied

### Code Change: `web_app/google_oauth.py`

**Before**:
```python
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=[...],
    # No redirect_uri specified
)
```

**After**:
```python
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=[...],
    redirect_to="google_auth.google_callback",
    redirect_url="/auth/google/authorized"
)
```

**Why This Helps**: Explicitly tells Flask-Dance where Google should redirect users after authentication.

---

## 🔧 Required Setup in Google Cloud Console

### Step 1: Create OAuth 2.0 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create a new one)
3. Navigate to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth client ID**
5. Choose **Web application**

### Step 2: Configure Authorized Redirect URIs

**CRITICAL**: Add these exact URIs to your OAuth client:

#### For Local Development:
```
http://localhost:5000/auth/google/authorized
http://127.0.0.1:5000/auth/google/authorized
http://localhost:5000/login/google/authorized
http://127.0.0.1:5000/login/google/authorized
```

#### For Production (Render/Deployed):
```
https://your-app-name.onrender.com/auth/google/authorized
https://your-app-name.onrender.com/login/google/authorized
```

**Replace `your-app-name` with your actual Render app name.**

### Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** (for public apps) or **Internal** (for organization only)
3. Fill in required fields:
   - **App name**: AI Learning Path Generator
   - **User support email**: Your email
   - **Developer contact**: Your email
4. Add scopes:
   - `openid`
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
5. Add test users (if in testing mode)

### Step 4: Copy Credentials to `.env`

After creating the OAuth client, copy the credentials:

```bash
# .env file
GOOGLE_OAUTH_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret-here
```

---

## 🔍 Verify Your Configuration

### Check 1: Environment Variables Loaded

Look at your terminal output when Flask starts. You should see:
```
INFO:google_oauth:ENV: GOOGLE_OAUTH_CLIENT_ID=...
```

**If you DON'T see this**, your `.env` file isn't being loaded or the variable names are wrong.

### Check 2: Correct Variable Names

In your `.env` file, make sure you're using:
- `GOOGLE_OAUTH_CLIENT_ID` (not `GOOGLE_CLIENT_ID`)
- `GOOGLE_OAUTH_CLIENT_SECRET` (not `GOOGLE_CLIENT_SECRET`)

### Check 3: No Extra Spaces or Quotes

```bash
# ❌ WRONG
GOOGLE_OAUTH_CLIENT_ID = "123456.apps.googleusercontent.com"

# ✅ CORRECT
GOOGLE_OAUTH_CLIENT_ID=123456.apps.googleusercontent.com
```

### Check 4: Redirect URI Matches Exactly

In Google Cloud Console, the redirect URI must match **character-for-character**:
- Protocol: `http://` vs `https://`
- Domain: `localhost` vs `127.0.0.1`
- Port: `:5000` (include if using non-standard port)
- Path: `/auth/google/authorized` (exact match)

---

## 🧪 Testing the Fix

### Test Locally

1. **Restart Flask** (important - environment changes need restart):
   ```bash
   # Stop the current server (Ctrl+C)
   python run.py
   ```

2. **Navigate to register page**:
   ```
   http://localhost:5000/auth/register
   ```

3. **Click "Continue with Google"**

4. **Expected Flow**:
   - Redirects to Google login page
   - You log in with your Google account
   - Google redirects back to your app at `/auth/google/authorized`
   - You're logged in and redirected to homepage

### Common Errors & Solutions

#### Error: "redirect_uri_mismatch"
**Cause**: The redirect URI in your code doesn't match Google Cloud Console  
**Fix**: Add the exact URI shown in the error to your OAuth client's authorized redirect URIs

#### Error: "invalid_client"
**Cause**: Client ID or Secret is wrong  
**Fix**: Double-check credentials in `.env` match Google Cloud Console

#### Error: "access_denied"
**Cause**: User clicked "Cancel" or app isn't approved  
**Fix**: Normal behavior if user cancels; if app needs approval, publish OAuth consent screen

#### Error: "unauthorized_client"
**Cause**: OAuth client not configured for web applications  
**Fix**: Recreate OAuth client as "Web application" type

---

## 📋 Checklist Before Testing

- [ ] Created OAuth 2.0 client in Google Cloud Console
- [ ] Added redirect URIs to OAuth client (both localhost and production)
- [ ] Configured OAuth consent screen
- [ ] Copied Client ID and Secret to `.env`
- [ ] Verified variable names: `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET`
- [ ] No quotes or extra spaces in `.env`
- [ ] Restarted Flask server after changing `.env`
- [ ] Checked terminal logs for environment variable loading

---

## 🔐 Security Best Practices

### Never Commit Credentials

Your `.env` file should be in `.gitignore`:
```
# .gitignore
.env
*.env
```

### Use Environment Variables in Production

On Render or other platforms:
1. Go to your app's **Environment** settings
2. Add `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET`
3. Don't use the `.env` file in production

### Rotate Secrets Regularly

If credentials are ever exposed:
1. Delete the OAuth client in Google Cloud Console
2. Create a new one
3. Update `.env` with new credentials

---

## 🐛 Debug Mode

If still having issues, enable detailed logging:

```python
# In web_app/google_oauth.py, add at the top:
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show detailed OAuth flow information in your terminal.

---

## 📚 Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Flask-Dance Documentation](https://flask-dance.readthedocs.io/)
- [Common OAuth Errors](https://developers.google.com/identity/protocols/oauth2/web-server#error-codes)

---

## 🎯 Expected Behavior After Fix

1. User clicks "Continue with Google" on register/login page
2. Redirects to Google's official login page
3. User logs in with Google credentials (on Google's domain)
4. Google redirects back to: `http://localhost:5000/auth/google/authorized`
5. Your app receives user's email and profile
6. App creates/finds user in database
7. User is logged in and redirected to homepage

---

## 🔄 Next Steps

1. **Verify `.env` file** has correct credentials
2. **Check Google Cloud Console** redirect URIs match
3. **Restart Flask server**
4. **Test the flow** by clicking "Continue with Google"
5. **Check terminal logs** for any error messages

If you still see the 400 error after these steps, share:
- The exact error message from Google
- Your redirect URI from the error
- Whether environment variables are loading (check terminal logs)

---

*Last Updated: 2025-10-04 20:49 CST*  
*Version: 1.0 - Initial OAuth Setup Guide*
