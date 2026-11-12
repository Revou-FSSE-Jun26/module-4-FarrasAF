---
inclusion: always
---

# Technology Stack

Architecture, data models, and API contracts live in the spec
(`.kiro/specs/task-management-app/design.md`). This file defines the stack,
tooling, and technical rules that apply to all work.

## Stack
- **Frontend**: Next.js (App Router), React, TypeScript, Tailwind CSS
- **Drag-and-drop**: `@dnd-kit/core` and `@dnd-kit/sortable`
- **Backend**: Python 3.14, Flask (application factory + blueprints), REST JSON API
- **Backend libraries**: Flask-SQLAlchemy, Flask-Migrate, PyJWT, `psycopg[binary]` (PostgreSQL driver), `python-dotenv`, `gunicorn`, `argon2-cffi`
- **Database**: PostgreSQL (local install for development, Supabase-hosted
  Postgres in production; no Docker), SQLAlchemy ORM, Alembic migrations
- **Auth**: JWT access tokens (15 minutes) + hashed, revocable refresh tokens (7 days), both delivered as `HttpOnly` cookies. Passwords hashed with argon2 (`argon2-cffi`).
- **Real-time**: none. Notifications use HTTP polling (no WebSockets in V1).

## Testing
- **Backend**: `pytest` + `hypothesis` (property-based tests)
- **Frontend**: Playwright end-to-end tests are the primary frontend test type
  (required by the course assignment). Cover the main user flows: auth,
  board/column/card CRUD, drag-and-drop, comments and mentions, search, and
  Guest access via Invitation Link.
- Every correctness property in `design.md` maps to exactly one backend
  property test, min 100 generated cases, tagged with:
  `# Feature: task-management-app, Property {n}: {text}`
- Pure logic (ordering, cursor codec, RBAC decision, analytics math) is kept
  in side-effect-free functions so it can be tested without the database.
- DB-backed tests use a transactional test database with rollback per test.
- E2E tests run against a dedicated test database seeded by a seed script.
  Tests must not depend on each other's data.
- E2E tests live in `frontend/e2e/`.

## Tooling
- **Python**: `ruff` (lint + format), `mypy` (type checking); type hints
  required on all public functions. Dependencies via `pip` + `requirements.txt`
  inside a virtual environment (`venv`).
- **TypeScript**: strict mode; never use `any`. See `frontend.md` for
  TypeScript rules. `eslint` + `prettier` (with prettier-plugin-tailwindcss).
- **Frontend deps**: `npm`
- **Local env**: local PostgreSQL; connection and secrets via `.env`

## Common Commands
```bash
# Backend (run from backend/)
cd backend
flask --app flask_app.app run --debug
flask --app flask_app.app db upgrade
python -m scripts.seed
pytest
ruff check . && ruff format . && mypy .

# Frontend (run from frontend/)
cd frontend
npm run dev
npm run lint
npm run build
npx playwright install # first time only
npx playwright test
```

## Technical Rules
- **Layering**: routes are thin; business logic lives in service modules;
  data access goes through SQLAlchemy models. No business logic in routes
  or in React components.
- **Transactions**: every mutating request runs in a single DB transaction.
  Activity_Entry and Notification writes happen in the same transaction as
  the triggering mutation.
- **Errors**: services raise typed domain errors, mapped centrally to the JSON error envelope. See `card-conventions.md` (rule 2) and the Error Handling section of `design.md`.
- **Auth order**: authentication gate first, then RBAC. The access token is read from its cookie and carries identity only; the Board role is read from stored membership on every request.
- **Health**: `GET /api/health` is public, returns 200, and never touches
  the database.
- **Concurrency**: Card and Comment updates require a `version` and use
  conditional `UPDATE ... WHERE version = :expected`.
- **Validation**: validate on the server always; trim before length checks.
  Frontend validation is for UX only.
- **JSON naming**: API JSON uses camelCase; database columns and Python
  code use snake_case. Conversion happens in one serialization helper in
  `backend/flask_app/common/`; services and routes never rename fields by
  hand. Frontend types in `frontend/src/types/api.ts` use camelCase.
- **Time**: store and compute all timestamps in UTC.
- **Pagination**: cursor-based for Notifications, page-index for Activity.
  Page sizes and caps are enforced server-side.
- **Performance**: no N+1 queries (use eager loading); index per `design.md`;
  target p95 < 300 ms for regular requests.

## Security
- Never log or return passwords, tokens, or hashes.
- Secrets and config come from environment variables; never commit `.env`
  (provide `.env.example`).
- Login errors are generic and never reveal whether the email, password, or
  lockout state was the cause.
- Refresh tokens are stored hashed; invitation tokens are high-entropy.
- Tokens live only in `HttpOnly` cookies: never in response bodies, URLs,
  or browser storage. Cookies use `SameSite=Lax`, no `Domain` attribute, and
  `Secure` controlled by a `COOKIE_SECURE` env var (true in production).
  The refresh cookie is scoped to `/api/auth/refresh` and `/api/auth/logout`.
- State-changing requests never use GET (CSRF protection relies on
  `SameSite=Lax`).
- No CORS configuration: the browser only talks to the frontend origin,
  which proxies `/api/*` to the backend.

## Deployment
- Deployed for the course assignment: frontend on Vercel, backend on Render,
  both from this monorepo. Each service sets its own Root Directory
  (`frontend/`, `backend/`).
- Backend runs on a Render Web Service with the native Python runtime
  (no Docker). Build: `pip install -r requirements.txt`. Start:
  `gunicorn "flask_app.app:create_app()"`. Never use `flask run` in
  production. Python version is set with the `PYTHON_VERSION` env var (a fully qualified 3.14 version such as 3.14.3).
- Production database is Supabase Postgres, used only as a plain PostgreSQL
  database. Connect through the Session pooler string (port 5432) from the
  Connect dialog, with `sslmode=require`; use the `postgresql+psycopg://`
  scheme for SQLAlchemy and URL-encode special characters in the password.
  The connection string comes from `DATABASE_URL`.
- Supabase Free projects pause after a week of inactivity. Check that the
  project is active (restore it from the dashboard if needed) before demos.
- Migrations and seeding are run manually from a developer machine against
  the production `DATABASE_URL` (`flask --app flask_app.app db upgrade`,
  `python -m scripts.seed`); never at request time.
- The browser only calls same-origin `/api/*` paths. `frontend/next.config.ts`
  rewrites `/api/:path*` to the backend URL from the server-side `API_URL`
  env var (not `NEXT_PUBLIC_`); paths are identical on both sides. Locally,
  `API_URL` points to the local Flask server.
- Secrets (`JWT_SECRET_KEY`, `DATABASE_URL`, etc.) are set as platform
  environment variables, never committed. Production runs with debug off.
- Free-tier backend sleeps when idle; the first request after idle may be
  slow, and a proxied request may time out while the backend wakes. Open
  `/api/health` before demos.
- Playwright E2E tests run locally or in CI against a test database, not
  against production.

## Constraints
- Do not add dependencies outside this stack without an explicit spec change.
- Do not introduce Docker, file storage, email, WebSockets, or third-party
  integrations (see Non-Goals in `product.md`).
- Do not hand-edit applied Alembic migrations; add a new one instead.
- Do not use Supabase client libraries, Supabase Auth, Storage, Realtime, or
  the auto-generated Data API. The app uses its own JWT authentication and
  talks to Postgres only through SQLAlchemy.
- Do not call the backend URL directly from browser code and do not add CORS.