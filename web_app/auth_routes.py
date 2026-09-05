"""Session/auth support routes.

The Jinja-rendered ``/auth/login`` and ``/auth/register`` pages were part of the
old purple UI and have been removed. React talks to the JSON API in
``web_app.auth_api`` instead (``/api/auth/register``, ``/api/auth/login``,
``/api/auth/logout``, ``/api/auth/me``).

What stays here is the machinery those endpoints -- and Google OAuth -- depend on:
the Flask-Login ``user_loader``, a browser-safe logout, and the username
availability check.
"""
import random

from flask import Blueprint, jsonify, redirect, request

from flask_login import current_user, logout_user

from web_app import db, login_manager
from web_app.frontend import frontend_url
from web_app.models import User

bp = Blueprint('auth', __name__)


# Required by Flask-Login to restore ``current_user`` from the session cookie.
# This is what makes "refresh the React page and stay signed in" work.
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@bp.route('/logout')
def logout():
    """Browser-navigable logout.

    Kept for links that perform a full page navigation (and for the OAuth flow).
    React's own sign-out button uses ``POST /api/auth/logout`` and stays in-app.
    Always lands the user back on the React frontend, never on a Flask page.
    """
    if current_user.is_authenticated:
        logout_user()
    return redirect(frontend_url('/login'))


@bp.route('/check-username', methods=['POST'])
def check_username():
    """Check if a username is available and suggest alternatives if not."""
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()

    if len(username) < 3:
        return jsonify({
            'available': False,
            'message': 'Username must be at least 3 characters long'
        })

    user = User.query.filter_by(username=username).first()
    if user is not None:
        base = username
        suggestions = [
            f"{base}{random.randint(1, 999)}",
            f"awesome_{base}",
            f"{base}_learner"
        ]

        return jsonify({
            'available': False,
            'message': 'This username is already taken',
            'suggestions': suggestions
        })

    return jsonify({
        'available': True,
        'message': 'Username is available!'
    })
