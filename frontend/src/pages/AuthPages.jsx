import { useEffect, useState } from 'react';
import { ArrowRight, LockKeyhole, Mail, Sparkles, UserRound } from 'lucide-react';
import { startGoogleLogin } from '../auth/authApi';
import { linkHandler, navigate } from '../lib/navigation';
import { useAuth } from '../auth/AuthContext';

/** Where to land after a successful sign-in, honouring ?next= if it is safe. */
function nextDestination() {
  const next = new URLSearchParams(window.location.search).get('next');
  // Only same-origin, app-relative paths. Never trust this into an absolute URL.
  return next && next.startsWith('/') && !next.startsWith('//') ? next : '/dashboard';
}

/** Field-level errors returned by the Flask validators. */
function FieldErrors({ fields }) {
  const messages = Object.values(fields || {}).flat();
  if (!messages.length) return null;
  return <ul className="auth-error">{messages.map((message) => <li key={message}>{message}</li>)}</ul>;
}

function AuthFrame({ eyebrow, title, copy, children }) {
  return <main className="auth-screen"><div className="auth-glow" /><section className="auth-card glass-panel"><div className="auth-brand"><span className="brand-mark"><Sparkles size={16} /></span><strong>learn<span className="accent-text">/ai</span></strong></div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p className="auth-copy">{copy}</p>{children}</section></main>;
}

function useRedirectIfAuthenticated() {
  const { user, loading } = useAuth();
  useEffect(() => { if (!loading && user) navigate(nextDestination(), { replace: true }); }, [loading, user]);
  return { user, loading };
}

export function LoginPage() {
  const { login } = useAuth();
  const { user, loading: authLoading } = useRedirectIfAuthenticated();
  const [email, setEmail] = useState(''); const [password, setPassword] = useState(''); const [rememberMe, setRememberMe] = useState(true); const [error, setError] = useState(''); const [fields, setFields] = useState({}); const [busy, setBusy] = useState(false);
  if (authLoading || user) return <AuthLoading />;
  const submit = async (event) => { event.preventDefault(); setError(''); setFields({}); setBusy(true); try { await login({ email, password, rememberMe }); navigate(nextDestination(), { replace: true }); } catch (loginError) { setError(loginError.message); setFields(loginError.fields || {}); } finally { setBusy(false); } };
  return <AuthFrame eyebrow="WELCOME BACK" title="Continue your learning." copy="Sign in to pick up exactly where you left off."><form className="auth-form" onSubmit={submit}><label><Mail size={15} /> Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" /></label><label><LockKeyhole size={15} /> Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required autoComplete="current-password" /></label><label className="auth-check"><input type="checkbox" checked={rememberMe} onChange={(event) => setRememberMe(event.target.checked)} /> Keep me signed in</label>{error && <p className="auth-error">{error}</p>}<FieldErrors fields={fields} /><button className="button button-primary auth-submit" disabled={busy}>{busy ? 'Signing in...' : 'Sign in'} <ArrowRight size={16} /></button></form><div className="auth-divider">or</div><button className="button button-secondary auth-submit" onClick={startGoogleLogin}>Continue with Google</button><p className="auth-foot">New here? <a href="/register" onClick={linkHandler('/register')}>Create an account</a></p><p className="auth-foot"><a href="/forgot-password" onClick={linkHandler('/forgot-password')}>Forgot password?</a></p></AuthFrame>;
}

export function RegisterPage() {
  const { register } = useAuth(); const { user, loading: authLoading } = useRedirectIfAuthenticated();
  const [form, setForm] = useState({ displayName: '', username: '', email: '', password: '', password2: '' }); const [error, setError] = useState(''); const [fields, setFields] = useState({}); const [busy, setBusy] = useState(false);
  if (authLoading || user) return <AuthLoading />;
  const update = (field) => (event) => setForm((previous) => ({ ...previous, [field]: event.target.value }));
  const submit = async (event) => {
    event.preventDefault(); setError(''); setFields({});
    if (form.password !== form.password2) { setError('Passwords must match.'); return; }
    setBusy(true);
    try { await register(form); navigate('/dashboard', { replace: true }); }
    catch (registerError) { setError(registerError.message); setFields(registerError.fields || {}); }
    finally { setBusy(false); }
  };
  return <AuthFrame eyebrow="START YOUR JOURNEY" title="Make learning personal." copy="Create your account and keep every path, milestone, and conversation connected."><form className="auth-form" onSubmit={submit}><label><UserRound size={15} /> Name<input value={form.displayName} onChange={update('displayName')} required autoComplete="name" /></label><label>Username<input value={form.username} onChange={update('username')} required minLength="3" autoComplete="username" /></label><label><Mail size={15} /> Email<input type="email" value={form.email} onChange={update('email')} required autoComplete="email" /></label><label><LockKeyhole size={15} /> Password<input type="password" value={form.password} onChange={update('password')} required minLength="8" autoComplete="new-password" /></label><label><LockKeyhole size={15} /> Confirm password<input type="password" value={form.password2} onChange={update('password2')} required minLength="8" autoComplete="new-password" /></label>{error && <p className="auth-error">{error}</p>}<FieldErrors fields={fields} /><button className="button button-primary auth-submit" disabled={busy}>{busy ? 'Creating account...' : 'Create account'} <ArrowRight size={16} /></button></form><div className="auth-divider">or</div><button className="button button-secondary auth-submit" onClick={startGoogleLogin}>Continue with Google</button><p className="auth-foot">Already have an account? <a href="/login" onClick={linkHandler('/login')}>Sign in</a></p></AuthFrame>;
}

export function AuthLoading() { return <main className="auth-screen"><div className="auth-loading"><Sparkles size={22} className="spin" /><p>Checking your session...</p></div></main>; }
export function UnauthorizedPage() { useEffect(() => { navigate(`/login?next=${encodeURIComponent(window.location.pathname)}`, { replace: true }); }, []); return <AuthLoading />; }
export function ForgotPasswordPage() { return <AuthFrame eyebrow="ACCOUNT HELP" title="Password reset is not configured yet." copy="This project currently supports password login and Google OAuth, but it has no password-reset endpoint. Use Google login or contact the account administrator."><a className="button button-secondary auth-submit" href="/login" onClick={linkHandler('/login')}>Back to sign in <ArrowRight size={16} /></a></AuthFrame>; }
