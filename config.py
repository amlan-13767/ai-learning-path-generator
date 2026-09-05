import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
# Load .env file only if not on Render
if not os.environ.get('RENDER'):
    load_dotenv(os.path.join(basedir, '.env'))

# Set Flask app for CLI commands (needed for flask db upgrade)
os.environ.setdefault('FLASK_APP', 'run.py')

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError('FLASK_SECRET_KEY must be set before starting the application.')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError('DATABASE_URL must be set; SQLite fallback is disabled.')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'  # Default for local development
    PERMANENT_SESSION_LIFETIME = 7200  # 2 hours
    SESSION_REFRESH_EACH_REQUEST = True  # Refresh session on each request
    SESSION_USE_SIGNER = True  # Sign session cookies for security
    SESSION_COOKIE_NAME = 'learning_path_session'  # Custom session cookie name
    
    # Ensure cookies work with OAuth redirects in production
    if os.environ.get('RENDER'):
        SESSION_COOKIE_SECURE = True       # Cookie only over HTTPS
        SESSION_COOKIE_SAMESITE = 'None'   # Allow cross-site OAuth redirect
        REMEMBER_COOKIE_SECURE = True
        REMEMBER_COOKIE_SAMESITE = 'None'
    else:
        # Local development - allow HTTP cookies
        SESSION_COOKIE_SECURE = False
        REMEMBER_COOKIE_SECURE = False
        
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
