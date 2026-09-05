# Single-Frontend Refactor Report

Flask is now backend/API only. React (Liquid Glass) is the one user-facing
application. The Liquid Glass design was not touched.

---

## Root causes

### 1. React navigating to `http://localhost:5000/` (the purple UI)

Two independent paths caused this.

**Primary — `frontend/src/App.jsx:70`:**

```js
const handleSubmit = async (formData) => {
  if (!user) {
    window.location.href = `${API_BASE_URL}/auth/login?next=/`;   // <-- port 5000
    return;
  }
```

`API_BASE_URL` resolved to `http://localhost:5000`, so clicking **Generate my
learning path** while logged out performed a full-page navigation to the Flask
Jinja login page. Because registration was broken (cause 2), `user` was always
`null`, so this fired on essentially every attempt.

**Secondary — Flask-Login redirect.** `login_manager.login_view = 'auth.login'`
meant `@login_required` on `/api/generate` answered with `302 -> /auth/login`.
Axios follows redirects transparently, so React received the old login page's
HTML where it expected JSON.

**Fixed by:** replacing the navigation with in-app `navigate('/login?next=/build')`;
setting `login_view = None` and registering an `unauthorized_handler` that
returns JSON `401`; adding an axios interceptor that flags 401s so callers route
to React's own `/login`.

### 2. React registration always failing

`frontend/src/auth/authApi.js` fetched the Flask **HTML** register page,
regex-scraped `csrf_token` out of the markup, POSTed
`application/x-www-form-urlencoded`, then guessed success from `response.url`.

This cannot work cross-origin. `config.py` sets `SESSION_COOKIE_SAMESITE = 'Lax'`,
and `127.0.0.1:3000` -> `localhost:5000` is a cross-site request, so the browser
never returned the session cookie on the POST. The CSRF token therefore never
matched a session, Flask re-rendered the register page, `response.url` still
contained `/auth/register`, and the client reported the hardcoded string
*"Registration failed. Check your details and try again."* — regardless of the
real cause.

The same SameSite problem silently broke session restoration on refresh.

**Fixed by:** a real JSON auth API (`web_app/auth_api.py`) plus routing all
browser traffic through the Vite dev proxy so the session cookie is first-party.

---

## Additional defects found and fixed (not in the original brief)

| Defect | Impact |
|---|---|
| `/api/generate-task` and `/api/task-status/<id>` had **no `@login_required` and no ownership check** | Any user could read any other user's generated learning path by job ID — a direct violation of the user-isolation requirement |
| `main_routes.py` used `Queue(...)` but **never imported `rq.Queue`** | Both endpoints above raised `NameError` on every call; they had never worked |
| `web_app/__init__.py` passed `ssl_cert_reqs=None` to `redis.from_url()` for **plain `redis://` URLs** | redis-py raises on connect; broke the RQ queue under Docker (`REDIS_URL=redis://redis:6379`). `backend/routes.py` already guarded this correctly — the two are now consistent |
| `_store_anonymous_path` / `_load_anonymous_path` called in 4 places, **defined nowhere** | Latent `NameError`s in the old UI code (removed with it) |
| `/download/<path_id>` fell back to `session['current_path']` when the DB lookup failed | Ownership bypass; now returns JSON 404 |
| Heavy `src.*` imports at module scope | The Flask API could not start without the full LangChain/ML stack. Now lazy, so the API boots and is testable standalone |

---

## FILES DELETED

**Old Jinja templates (11)** — `web_app/templates/`: `index.html`,
`dashboard.html`, `result.html`, `login.html`, `register.html`, `agents.html`,
`404.html`, `500.html`, and three `.backup` files.

**Old purple CSS/JS (8)** — `web_app/static/`: `css/style.css`,
`css/glassmorphic.css`, `css/agents.css`, `js/app.js`, `js/agents.js`,
`js/milestone-tracker.js`, `js/sse-progress.js`, `js/theme.js`.

**Dead React files (2)** — `frontend/src/LegacyExperience.jsx` (imported by
nothing; linked to `${API_BASE_URL}/dashboard` and `/login/google`),
`frontend/src/TestPage.jsx`.

**Dev script (1)** — `fix_colors.py` (recoloured the deleted templates).

## OLD ROUTES REMOVED

| Route | Was |
|---|---|
| `GET /` | `render_template('index.html')` — purple home |
| `POST /generate` | Jinja form handler -> `/result` |
| `POST /generate-stream` | SSE feed for `sse-progress.js` |
| `GET /dashboard` | `render_template('dashboard.html')` |
| `GET /result` | `render_template('result.html')` |
| `GET /my-paths` | `render_template('login.html')` |
| `GET /path/<id>` | redirect to `/result` |
| `GET|POST /save_path` | session/flash save -> old dashboard |
| `POST /clear_session` | old UI session reset |
| `GET|POST /auth/register` | `render_template('register.html')` |
| `GET|POST /auth/login` | `render_template('login.html')` |

Supporting helpers removed: `index`, `generate_path`, `generate_stream`,
`save_learning_path`, `load_learning_path` (dead), `my_paths`, `dashboard`,
`result`, `view_path`, `clear_session_route`, `get_path_generator`,
`inject_current_year`. `main_routes.py`: 2212 -> 1548 lines.

## BACKEND FILES KEPT

`web_app/models.py`, `web_app/auth_forms.py`, `web_app/api_endpoints.py`,
`web_app/google_oauth.py`, `backend/routes.py`, `backend/app.py`, `worker/`,
`worker.py`, `migrations/`, `config.py`, `src/`, all Dockerfiles,
`docker-compose.dev.yml`. No models, migrations, generation logic, chat logic,
OAuth, Redis, worker, or PostgreSQL usage was removed.

## FILES MODIFIED

**Backend**
- `web_app/__init__.py` — app created with `static_folder=None, template_folder=None`;
  JSON `/` status route; JSON 404/500 handlers; JSON `unauthorized_handler`;
  registers the new auth API; Redis TLS-kwarg guard; `FRONTEND_URL` config.
- `web_app/auth_routes.py` — Jinja pages removed; keeps `user_loader`,
  `check-username`, and a logout that redirects **into React**.
- `web_app/main_routes.py` — old UI routes removed; `rq.Queue` imported;
  ownership + `@login_required` added to the two task endpoints; `/download`
  returns JSON errors; heavy imports made lazy.
- `web_app/api_endpoints.py` — `DocumentStore` imported lazily.
- `web_app/google_oauth.py` — all callback outcomes redirect to `FRONTEND_URL`.
- `web_app/routes/agents.py` — dropped unused `render_template` import.
- `docker-compose.dev.yml`, `.env.example` — added `FRONTEND_URL`.

**New backend files**
- `web_app/auth_api.py` — the JSON auth API.
- `web_app/frontend.py` — `frontend_url()` helper.

**Frontend**
- `frontend/src/lib/api.js` — `API_BASE_URL` defaults to `''` (same-origin);
  401 interceptor.
- `frontend/src/auth/authApi.js` — rewritten; no HTML scraping.
- `frontend/src/auth/AuthContext.jsx` — matches the new return shape; logout
  clears state even if the network call fails.
- `frontend/src/App.jsx` — the redirect bug fixed; reactive pathname.
- `frontend/src/pages/AuthPages.jsx` — field-level errors; safe `?next=`
  handling; the "Open existing Flask login" link removed.
- `frontend/vite.config.js` — proxies `/api`, `/auth`, `/login/google`, `/health`.
- `frontend/.env`, `.env.example` — `VITE_API_URL` empty, `VITE_BACKEND_ORIGIN` added.

**New frontend file**
- `frontend/src/lib/navigation.js` — `navigate()`, `usePathname()`, `linkHandler()`.
  `navigate()` throws on any non-relative path, so a `localhost:5000` regression
  fails loudly instead of silently.

**Tests**
- `tests/test_auth_ownership.py` — registration test moved to the JSON API.
- `tests/test_react_api_contract.py` — **new**, 22 tests.

---

## API ENDPOINTS USED BY REACT

| Purpose | Endpoint |
|---|---|
| Register | `POST /api/auth/register` |
| Login | `POST /api/auth/login` |
| Logout | `POST /api/auth/logout` |
| Session restore | `GET /api/auth/me`, `GET /api/me` |
| Google OAuth start | `GET /auth/google` (full-page, by design) |
| Queue generation | `POST /api/generate` |
| Poll job | `GET /api/status/<task_id>` |
| Fetch result | `GET /api/result/<task_id>` |
| List paths | `GET /api/paths` |
| Load path + progress | `GET /api/paths/<path_id>` |
| Save path | `POST /api/save-path` |
| Milestone progress | `POST /api/track-milestone` |
| AI tutor | `POST /api/ask` |
| Health | `GET /health` |

All return JSON. None returns HTML or a redirect.

## AUTHENTICATION FLOW

```
React /register  -> POST /api/auth/register (JSON)
                 -> RegistrationForm validators (unchanged)
                 -> User row in PostgreSQL, password hashed
                 -> login_user() sets the Flask session cookie
                 -> 201 { authenticated: true, user }
                 -> React navigate('/dashboard')        [stays on :3000]
```

One auth system only: Flask-Login + WTForms + PostgreSQL. No Firebase, MongoDB,
Supabase or Auth0. Passwords are never stored client-side; the only credential
in the browser is the HttpOnly Flask session cookie.

**CSRF.** The project never enabled a global `CSRFProtect`, and every
pre-existing `/api/*` POST already accepted a cookie-authenticated JSON body
with no token. The new endpoints match that model and add one hardening step:
they **require `Content-Type: application/json`** (415 otherwise). That forces a
CORS preflight for cross-origin attempts, which the origin allow-list rejects,
and a plain cross-site HTML form cannot produce a JSON content-type. Covered by
`test_auth_endpoints_require_json_content_type`.

## SESSION PERSISTENCE

The real reason refresh used to log you out was cookie scope, not code.
`SameSite=Lax` blocks the session cookie on cross-site XHR, and
`127.0.0.1:3000` -> `localhost:5000` is cross-site.

The fix is to stop making cross-origin requests at all: `VITE_API_URL` is now
empty, so the browser calls `/api/...` on its own origin and the Vite dev server
proxies to Flask. The cookie is first-party. Verified live — registering through
`127.0.0.1:3000` sets `learning_path_session` on host `127.0.0.1`, and a
subsequent `/api/auth/me` through the proxy returns the authenticated user.

`withCredentials: true` is set on the axios instance, consistent with the
project's existing choice.

## DATABASE / PERSISTENCE FLOW

```
users -> user_learning_paths -> learning_progress
                             -> milestone_progress
                             -> resource_progress
                             -> chat_messages
```

`_save_path_for_user()` (`backend/routes.py`) writes the path with
`user_id=current_user.id` and seeds a `LearningProgress` row per milestone.
`GET /api/paths/<id>` merges `LearningProgress` and `MilestoneProgress` so
progress returns with the path.

## USER ISOLATION

Every ownership check is server-side, filtering on `user_id=current_user.id`.
RQ jobs are stamped with `job.meta['user_id']` at enqueue time and verified on
every status/result read. Verified live with two real accounts: User B receives
`404` (never `403`, which would confirm existence) on User A's path, progress,
download, chat, and job status; `GET /api/paths` returns `[]`.

## GENERATION FLOW

```
React /build -> POST /api/generate  (JSON, session cookie)
             -> RQ job on the 'learning-paths' queue in Redis
             -> { task_id, status: 'queued' }
             -> React polls GET /api/status/<id> every 3s
             -> worker runs worker.tasks.generate_learning_path_for_worker
             -> GET /api/result/<id> -> saved to PostgreSQL -> rendered in React
```

Redis + RQ + the existing worker are unchanged. No navigation leaves React at
any point.

**OpenAI quota** — left untouched as instructed. `_job_error()` already maps
`insufficient_quota` / `credit_balance_exhausted` to a clean user-facing message,
which React renders in its error panel. No mock data, no provider swap.

---

## TESTS EXECUTED

| Check | Result |
|---|---|
| `npm run lint` | **clean**, 0 warnings |
| `npm run build` | **success**, 222.75 kB JS / 35.72 kB CSS |
| `python -m compileall` (web_app, backend, worker, config) | **clean** |
| `pytest tests/test_auth_ownership.py tests/test_react_api_contract.py` | **30 passed** |
| App boots without LangChain installed | **yes** (43 routes) |
| `backend/app.py` boots with RQ blueprint | **yes** |

### Live HTTP verification (Flask :5000 + Vite :3000 + Redis)

| # | Test | Result |
|---|---|---|
| 1 | Registration via React | `201`, user created, session opened |
| 2 | Login / logout / re-login | `200` each; access revoked after logout |
| 3 | Session restored on later requests | authenticated, cookie first-party on `127.0.0.1` |
| 4 | Generate while logged out | JSON `401`, **no `Location` header** — no HTML redirect |
| 4b | Generate while logged in | job queued in Redis, polling returns `queued` |
| 5 | Save path -> logout -> login | path **and** milestone progress restored |
| 6 | User isolation | B gets `404` on all of A's resources; `/api/paths` -> `[]` |
| 7 | `http://localhost:5000/` | `{"status":"ok","service":"AI Learning Path Generator API"}`, zero HTML |
| 7b | `/dashboard` `/result` `/register` `/my-paths` `/save_path` `/clear_session` `/path/<id>` `/generate` `/generate-stream` `/static/*` | all `404` JSON |
| 8 | Repo sweep for old-UI references | only the intentional Google OAuth start remains |
| — | SPA routes `/login` `/register` `/dashboard` `/build` `/my-paths` on :3000 | all serve the React shell |

Pre-existing, unrelated: 8 failures in `tests/test_resource_validator.py`
(async URL-validation logic in `src/utils/`). **Confirmed identical on the
original code via `git stash`** — not a regression.

---

## REMAINING ISSUES

1. **OpenAI quota** — untouched as instructed. Generation jobs will fail until
   the account is funded; React shows the clean error.

2. **Google OAuth needs host consistency.** This flow must leave the SPA and
   return via Flask's callback, so it cannot use the dev proxy. The session
   cookie is set on the backend's hostname. **Test Google sign-in from
   `http://localhost:3000`, not `127.0.0.1:3000`**, so both ports share the
   `localhost` cookie host. Password auth works from either. Credentials were
   not fabricated; the flow is otherwise unverified.

3. **`.env` with live secrets is committed in the archive** (OpenAI key,
   `FLASK_SECRET_KEY`, Google OAuth client secret). **Rotate these.** `.env` is
   in `.gitignore` but is present in the uploaded zip.

4. **`web_app/routes/agents.py` is dead code** — never registered by
   `create_app()`. Left in place per the "do not delete backend code"
   instruction; its `agents.html` template is gone, so register it only after
   converting any HTML responses to JSON.

5. **Password reset is still unimplemented.** `/forgot-password` explains this
   rather than linking to the deleted Flask page.

6. **`requirements.txt` pins `pydantic==1.10.18` while `openai>=1.0` needs
   pydantic v2.** Pre-existing conflict, unrelated to this task, but it will
   bite on a clean install.

7. **Line endings.** The archive mixes CRLF and LF, so `git status` shows many
   files as modified that were never touched. Consider a `.gitattributes` with
   `* text=auto`.

8. **Orphaned vendored copy: `ai learning path generator/`** (directory name with
   spaces, at the repo root). This is a snapshot of an *older, separate* version
   of the whole project — its own `src/` and `web_app/` with its own
   `templates/` (including a purple `learning_path.html`). It is referenced by
   **no** code, config, Dockerfile or Procfile, and Flask never serves it, so it
   is not part of the running application and was left alone rather than deleted
   blind. If you want the purple markup gone from the repository entirely:

   ```bash
   git rm -r "ai learning path generator"
   ```

   Verified safe: `grep -rn "ai learning path generator" --include=*.py
   --include=*.js --include=*.jsx --include=*.yml .` returns nothing.
