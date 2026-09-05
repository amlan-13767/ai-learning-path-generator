"""
Unified Flask + React Application
Serves React frontend at root, Flask API routes, and OAuth
"""
import os
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create the main app using the existing web_app factory (includes DB, OAuth, routes)
from web_app import create_app
app = create_app()

# Register the lightweight API blueprint for RQ task orchestration under /api
from backend.routes import api_bp
app.register_blueprint(api_bp, url_prefix='/api')

# Enable CORS for the React frontend and allow cookies for auth
configured_origin = os.getenv('FRONTEND_ORIGIN', 'http://localhost:3000')
frontend_origins = list(dict.fromkeys([
    configured_origin,
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]))
CORS(
    app,
    resources={r"/*": {"origins": frontend_origins}},
    supports_credentials=True,
)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
