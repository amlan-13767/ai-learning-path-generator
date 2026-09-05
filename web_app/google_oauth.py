import os
from flask import Blueprint, redirect, url_for, current_app, session, request
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_login import current_user, login_user
from web_app.models import OAuth, User
from web_app import db
from web_app.frontend import frontend_url
import logging
from datetime import datetime

# Ensure local development can use HTTP for OAuth exchanges
if os.getenv("FLASK_ENV", "development") == "development" and not os.getenv("RENDER"):
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('google_oauth')

# Log environment variables only in debug mode
if os.getenv("DEBUG") == "True" and os.getenv("LOG_ENV_VARS") == "True":
    for key in os.environ:
        if 'SECRET' not in key and 'KEY' not in key:
            logger.info(f"ENV: {key}={os.environ.get(key)}")

# Create a very basic blueprint for Google OAuth
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ],
    redirect_to="google_auth.google_callback",
    redirect_url="/auth/google/authorized",
    storage=SQLAlchemyStorage(OAuth, db.session, user=current_user, user_required=False)
)


# Create a separate blueprint for our callback route
bp = Blueprint("google_auth", __name__)

# Add login helpers that point to the Flask-Dance blueprint
@bp.route("/login")
def login():
    return redirect(url_for("google.login"))


@bp.route("/google")
def start_google_login():
    """Route used by the UI to start Google OAuth."""
    return redirect(url_for("google.login"))

@bp.route("/google/authorized")
@bp.route("/callback/google")
@bp.route("/google-callback")
def google_callback():
    """Handle the callback from Google OAuth"""
    # Log important debug info
    logger.info(f"Google OAuth callback received at {request.path}")
    logger.info(f"Full request URL: {request.url}")
    logger.info(f"Request args: {request.args}")
    logger.info(f"Is Google authorized? {google.authorized}")
    
    # If this route is hit directly without going through OAuth flow
    if not google.authorized:
        logger.error("Not authorized. Redirecting to the React login page.")
        return redirect(frontend_url("/login?error=google_not_authorized"))

    # Get user info from Google
    try:
        resp = google.get("/oauth2/v2/userinfo")
        if not resp.ok:
            logger.error(f"Failed to fetch user info: {resp.text}")
            return redirect(frontend_url("/login?error=google_userinfo_failed"))

        info = resp.json()
        logger.info(f"Successfully retrieved user info")
        
        email = info.get("email")
        if not email:
            logger.error("Google account does not have an email.")
            return redirect(frontend_url("/login?error=google_no_email"))

        google_subject = info.get('id') or info.get('sub')
        # Prefer the provider subject, then fall back to the verified email.
        user = User.query.filter_by(google_subject=google_subject).first() if google_subject else None
        user = user or User.query.filter_by(email=email).first()
        if not user:
            logger.info(f"Creating new user: {email}")
            username_base = ''.join(char.lower() if char.isalnum() else '_' for char in (info.get('name') or email.split('@')[0])).strip('_') or 'learner'
            username = username_base
            suffix = 1
            while User.query.filter_by(username=username).first():
                suffix += 1
                username = f'{username_base}_{suffix}'
            user = User(
                username=username,
                email=email,
                registration_source='google',
                google_subject=google_subject,
                display_name=info.get('name')
            )
            db.session.add(user)
            db.session.commit()
        else:
            logger.info(f"Found existing user: {email}")
            if google_subject and user.google_subject != google_subject:
                user.google_subject = google_subject
            user.registration_source = user.registration_source or 'google'
            user.login_count = (user.login_count or 0) + 1
            user.last_seen = datetime.utcnow()

        pending_oauth = OAuth.query.filter_by(
            provider='google',
            user_id=None
        ).order_by(OAuth.created_at.desc()).first()
        if pending_oauth:
            pending_oauth.user_id = user.id
        db.session.commit()

        # Log the user in with a permanent session
        session.permanent = True
        login_user(user, remember=True, duration=None)
        
        # Land the user back inside the React application.
        return redirect(frontend_url("/dashboard"))
        
    except Exception as e:
        logger.exception(f"Error in Google callback: {str(e)}")
        # Check if it's a state mismatch error
        if "MismatchingStateError" in str(type(e).__name__) or "state" in str(e).lower():
            return redirect(frontend_url("/login?error=google_session_expired"))
        return redirect(frontend_url("/login?error=google_failed"))
