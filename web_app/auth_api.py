"""JSON authentication API consumed by the React (Liquid Glass) frontend.

This module deliberately does NOT introduce a second authentication system.
It is a thin JSON transport in front of the *existing* stack:

    * ``web_app.auth_forms.RegistrationForm`` / ``LoginForm``  -> validation rules
    * ``flask_login.login_user`` / ``logout_user``             -> session handling
    * ``web_app.models.User`` + PostgreSQL                     -> persistence

The old Jinja pages posted ``application/x-www-form-urlencoded`` bodies and
answered with redirects, which React cannot consume. These endpoints accept and
return JSON while running the exact same validators and writing to the exact
same tables.

CSRF note
---------
The project never enabled a global ``CSRFProtect``; the Jinja forms relied on
``FlaskForm``'s per-form token, and every pre-existing ``/api/*`` POST endpoint
(``/api/save-path``, ``/api/track-milestone``, ``/api/generate``) already accepts
a cookie-authenticated JSON body with no token. These endpoints follow the same
model, with one hardening step: they *require* ``Content-Type: application/json``.
That forces the browser to send a CORS preflight for any cross-origin attempt,
and the preflight is rejected for origins outside the allow-list configured in
``backend/app.py``. A plain cross-site HTML form cannot produce a JSON
content-type, so it cannot reach these routes.
"""
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_user, logout_user
from werkzeug.datastructures import MultiDict

from web_app import db
from web_app.auth_forms import LoginForm, RegistrationForm
from web_app.models import User

bp = Blueprint('auth_api', __name__, url_prefix='/api/auth')


def serialize_user(user):
    """Public user representation shared by every auth endpoint."""
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'display_name': user.display_name,
    }


def _require_json():
    """Return an error response if the request is not a JSON payload."""
    if not request.is_json:
        return jsonify({
            'error': 'This endpoint expects a JSON request body.',
        }), 415
    return None


def _form_errors(form):
    """Flatten WTForms errors into {field: [messages]} plus a headline message."""
    fields = {name: list(messages) for name, messages in form.errors.items()
              if name != 'csrf_token'}
    first = next((messages[0] for messages in fields.values() if messages), None)
    return {
        'error': first or 'Please correct the highlighted fields and try again.',
        'fields': fields,
    }


@bp.route('/register', methods=['POST'])
def register():
    """Create an account, then log the new user straight in.

    Accepts both snake_case and camelCase keys so the React form can post its
    own state object without an extra mapping layer.
    """
    guard = _require_json()
    if guard:
        return guard

    payload = request.get_json(silent=True) or {}
    submitted = MultiDict({
        'display_name': payload.get('display_name') or payload.get('displayName') or '',
        'username': payload.get('username') or '',
        'email': payload.get('email') or '',
        'password': payload.get('password') or '',
        'password2': payload.get('password2') or payload.get('confirmPassword') or '',
    })

    # meta={'csrf': False}: this is a JSON API, not a browser form post.
    form = RegistrationForm(formdata=submitted, meta={'csrf': False})
    if not form.validate():
        return jsonify(_form_errors(form)), 400

    user = User(
        username=form.username.data,
        email=form.email.data,
        display_name=form.display_name.data,
    )
    user.set_password(form.password.data)
    user.registration_source = 'email_password'
    user.last_seen = datetime.utcnow()
    user.login_count = 1

    db.session.add(user)
    try:
        db.session.commit()
    except Exception:
        # Unique constraints are the realistic failure here (race on username/email).
        db.session.rollback()
        return jsonify({
            'error': 'That username or email is already registered.',
            'fields': {},
        }), 409

    login_user(user)
    return jsonify({'authenticated': True, 'user': serialize_user(user)}), 201


@bp.route('/login', methods=['POST'])
def login():
    """Authenticate against the existing password hashes and open a Flask session."""
    guard = _require_json()
    if guard:
        return guard

    payload = request.get_json(silent=True) or {}
    remember_me = bool(payload.get('remember_me', payload.get('rememberMe', True)))
    submitted = MultiDict({
        'email': payload.get('email') or '',
        'password': payload.get('password') or '',
    })

    form = LoginForm(formdata=submitted, meta={'csrf': False})
    if not form.validate():
        return jsonify(_form_errors(form)), 400

    user = User.query.filter_by(email=form.email.data).first()
    # Uniform message: do not reveal whether the address exists.
    if user is None or not user.check_password(form.password.data):
        return jsonify({'error': 'Email or password is incorrect.'}), 401

    login_user(user, remember=remember_me)
    user.last_seen = datetime.utcnow()
    user.login_count = (user.login_count or 0) + 1
    db.session.commit()

    return jsonify({'authenticated': True, 'user': serialize_user(user)}), 200


@bp.route('/logout', methods=['POST'])
def logout():
    """Clear the Flask session. Safe to call when already logged out."""
    logout_user()
    return jsonify({'authenticated': False}), 200


@bp.route('/me', methods=['GET'])
def me():
    """Session restoration endpoint: who is the session cookie for?"""
    if not current_user.is_authenticated:
        return jsonify({'authenticated': False}), 200
    return jsonify({'authenticated': True, 'user': serialize_user(current_user)}), 200
