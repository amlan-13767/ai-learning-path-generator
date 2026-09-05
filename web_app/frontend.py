"""Helpers for pointing server-side redirects back at the React frontend.

Flask is backend-only. The only time it may issue a *browser* redirect to a
user-facing page is at the end of an OAuth round-trip, and that redirect must
land on the React app -- never on a Flask-rendered page.
"""
from flask import current_app

DEFAULT_FRONTEND_URL = 'http://localhost:3000'


def frontend_url(path='/'):
    """Absolute URL of a route inside the React application.

    Configured via the ``FRONTEND_URL`` environment variable so that dev,
    Docker and production can each point somewhere different without code edits.
    """
    base = (current_app.config.get('FRONTEND_URL') or DEFAULT_FRONTEND_URL).rstrip('/')
    if not path.startswith('/'):
        path = '/' + path
    return base + path
