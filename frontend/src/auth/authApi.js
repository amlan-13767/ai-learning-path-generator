import api from '../lib/api';

/**
 * Absolute origin of the Flask backend.
 *
 * Only Google OAuth needs this: that flow has to leave the SPA, bounce through
 * Google, and come back to a Flask callback URL, so it cannot go through the
 * dev-server proxy. Every other request is same-origin (see lib/api.js).
 */
export const BACKEND_ORIGIN = import.meta.env.VITE_BACKEND_ORIGIN || 'http://localhost:5000';

/** Turn an axios failure into a message worth showing a human. */
function toAuthError(error) {
  if (!error.response) {
    return new Error('Cannot reach the server. Check that the Flask API is running.');
  }
  const data = error.response.data || {};
  const authError = new Error(data.error || 'Something went wrong. Please try again.');
  // Field-level messages from the Flask WTForms validators, e.g.
  // { username: ['This username is already taken. How about ...?'] }
  authError.fields = data.fields || {};
  throw authError;
}

export async function loginWithPassword({ email, password, rememberMe }) {
  try {
    const response = await api.post('/api/auth/login', {
      email,
      password,
      remember_me: Boolean(rememberMe),
    });
    return response.data.user;
  } catch (error) {
    return toAuthError(error);
  }
}

export async function registerWithPassword({ displayName, username, email, password, password2 }) {
  try {
    const response = await api.post('/api/auth/register', {
      display_name: displayName,
      username,
      email,
      password,
      password2,
    });
    return response.data.user;
  } catch (error) {
    return toAuthError(error);
  }
}

export async function logoutFromFlask() {
  await api.post('/api/auth/logout');
}

/**
 * Start the existing Flask Google OAuth flow.
 *
 * Flask's callback finishes by redirecting to FRONTEND_URL/dashboard, so the
 * user always lands back inside React.
 *
 * Note: because this leaves and re-enters the app via the Flask origin, the
 * session cookie is set on the backend's hostname. Open the app on
 * http://localhost:3000 (not 127.0.0.1) when testing Google sign-in so both
 * ports share the `localhost` cookie host.
 */
export function startGoogleLogin() {
  window.location.assign(`${BACKEND_ORIGIN}/auth/google`);
}
