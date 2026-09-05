import os
import redis
from rq import Queue
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import text

db = SQLAlchemy()
login_manager = LoginManager()
# No login_view: this process is a JSON API. A browser redirect to a Flask login
# page is exactly the bug we are fixing, so unauthenticated calls get a 401
# instead (see the unauthorized handler below) and React routes to its own
# /login page.
login_manager.login_view = None
login_manager.login_message = None
login_manager.login_message_category = 'info'
migrate = Migrate()


@login_manager.unauthorized_handler
def unauthorized():
    """Answer unauthenticated API calls with JSON 401, never an HTML redirect."""
    return jsonify({
        'authenticated': False,
        'error': 'Authentication required.',
    }), 401


def create_app(config_class=Config):
    # static_folder=None removes Flask's /static/<path> route entirely: the old
    # purple CSS/JS lived there and must not be reachable.
    # template_folder=None: nothing server-side renders HTML any more.
    app = Flask(__name__, static_folder=None, template_folder=None)
    app.config.from_object(config_class)

    # If the app is running behind a proxy (like on Render), fix the WSGI environment
    if os.environ.get('RENDER'):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Where the React frontend lives. Used only for OAuth return redirects.
    app.config.setdefault(
        'FRONTEND_URL',
        os.environ.get('FRONTEND_URL', 'http://localhost:3000'),
    )

    # Set DEV_MODE from environment
    app.config['DEV_MODE'] = os.environ.get('DEV_MODE', 'False').lower() == 'true'
    if app.config['DEV_MODE']:
        print("\033[93m⚠️  Running in DEV_MODE - API calls will be stubbed!\033[0m")

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Initialize Redis connection for RQ
    try:
        redis_url = os.environ.get('REDIS_URL')
        if not redis_url:
            raise ValueError("REDIS_URL not set, worker queue will not be available.")
        # ssl_cert_reqs is a TLS-only kwarg: passing it on a plain redis:// URL
        # makes redis-py raise when it opens the connection (which is lazy, so
        # it surfaced as a 500 on first use rather than at startup).
        # This mirrors the guard already present in backend/routes.py.
        if redis_url.startswith('rediss://'):
            app.redis = redis.from_url(redis_url, ssl_cert_reqs=None)
        else:
            app.redis = redis.from_url(redis_url)
        app.logger.info("Redis connection for RQ initialized successfully.")
    except Exception as e:
        app.logger.error(f"Failed to initialize Redis connection: {e}")
        app.redis = None

    # Import and register blueprints
    from web_app.main_routes import bp as main_bp
    app.register_blueprint(main_bp)

    from web_app.auth_routes import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # JSON auth API consumed by React (register / login / logout / me)
    from web_app.auth_api import bp as auth_api_bp
    app.register_blueprint(auth_api_bp)

    from web_app.api_endpoints import api_bp
    app.register_blueprint(api_bp)

    # Import models here to ensure they are registered with SQLAlchemy
    from web_app import models

    @app.route('/')
    def service_root():
        """Backend root. There is no user-facing page here any more."""
        return jsonify({
            'status': 'ok',
            'service': 'AI Learning Path Generator API',
            'frontend': app.config['FRONTEND_URL'],
        }), 200

    # Health endpoint for keep-alive (prevents Supabase auto-pause)
    @app.route('/health')
    def health():
        try:
            with app.app_context():
                with db.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
            return {"status": "ok", "db": "connected"}, 200
        except Exception as e:
            return {"status": "error", "db": str(e)}, 500

    @app.errorhandler(404)
    def not_found(error):
        """Every unknown path is an API miss, not a missing web page."""
        return jsonify({
            'error': 'Not found',
            'path': request.path,
            'service': 'AI Learning Path Generator API',
        }), 404

    @app.errorhandler(500)
    def server_error(error):
        app.logger.exception('Unhandled server error')
        return jsonify({'error': 'Internal server error'}), 500

    # Google OAuth blueprint (Flask-Dance)
    from web_app.google_oauth import google_bp, bp as google_auth_bp
    # Register Flask-Dance blueprint at /login/google
    app.register_blueprint(google_bp, url_prefix="/login")
    # Register our auth blueprint for callbacks and helper routes under /auth
    app.register_blueprint(google_auth_bp, url_prefix="/auth")

    # Flask-Dance will use session storage by default
    # This works better for our use case since we create the user in our callback

    return app
