# RevoTask

## Overview

RevoTask is a Trello-like task management application built through a disciplined AI-driven development workflow. Users create Teams and Boards, organize work into Columns, move Cards with drag-and-drop, collaborate through threaded Comments with @mentions, and follow activity and progress on each Board. Both the Flask API and the Next.js frontend are deployed.

- Frontend (Vercel): https://task-management-app-red-three.vercel.app
- Backend (Render): https://backend-task-management-app-cw2q.onrender.com

## AI Workflow Summary

The project followed a spec-driven workflow with Kiro, from brief to deployed code.

1. **Project brief.** I wrote `task-management-project-brief.txt` (repo root) first. It defines the product, the three Board roles (Guest, Member, Admin), and the core features.
2. **Specs.** In Kiro I used the brief to generate `requirements.md`, `design.md`, and `tasks.md` in `.kiro/specs/task-management-app/`. I reviewed each document and iterated on it with Kiro before moving to the next. Every later change went through the same documents and was recorded in `CHANGELOG.md` (currently v20, for example v20 added the user Profile requirement). Requirements, design, and tasks were checked against each other for contradictions after each change.
3. **Steering.** I wrote steering files in `.kiro/steering/`: `product`, `tech`, `structure`, `frontend`, `backend`, `database`, `card-conventions`, `development-workflow`, `change-management`, and `core`. They fix the stack, folder layout, naming, layering (thin routes, logic in services), error handling, and the Card invariants. Kiro loads them on every request, so generated code follows them.
4. **Code generation and review.** Kiro implemented the tasks in `tasks.md` one at a time. Each result was reviewed against the steering rules and the spec, and verified by tests.
5. **Violations.** When generated code broke a steering rule or a spec requirement, the fix was made in code and, where the spec or steering was unclear, in the spec or steering itself. Spec-level changes are recorded in `CHANGELOG.md`.
6. **Tests and documentation.** Kiro (in the IDE) generated and refined the pytest, Hypothesis and Playwright tests and the project documentation, including this README. Kiro CLI was not used in this project.

## Features Implemented

- Email and password authentication with JWT access and refresh tokens in `HttpOnly` cookies, and protected routes
- User profile: edit display name and change password
- Teams: create a Team and join through revocable Team Join Links
- Board and Column management (create, rename, reorder, delete, archive)
- Card create, edit, delete, and drag-and-drop move and reorder. Order is stored as a contiguous integer `order_index` per Column and reindexed after every move.
- Comment creation and editing, threaded replies, and @mentions
- Notifications with HTTP polling (every 30 seconds) and an unread badge on the bell
- Card search by title
- Activity Log per Board
- Board analytics
- Role-based access control (Admin, Member) and anonymous read-only Guest access through Invitation Links
- Playwright E2E suite covering auth, boards, drag-and-drop, comments, search, teams, profile, guest access, and responsive layout
- Backend pytest suite with unit, integration, and Hypothesis property tests

## Technologies Used

- **Frontend:** Next.js (App Router), React, TypeScript, Tailwind CSS, `@dnd-kit`, Playwright
- **Backend:** Flask, SQLAlchemy (Flask-SQLAlchemy), Flask-Migrate (Alembic), PyJWT, argon2-cffi, Marshmallow, python-dotenv, Gunicorn
- **Database:** PostgreSQL (Supabase Postgres in production)
- **Backend testing:** pytest, Hypothesis
- **Deployment:** Render (backend), Vercel (frontend)
- **AI tools:** Kiro

## How to Run Locally

Prerequisites: Python 3.14, Node.js with npm, and a local PostgreSQL server (no Docker).

1. Clone the repository and open it:

   ```powershell
   git clone <repository-url>
   cd task-management-app
   ```

2. Backend (from `backend/`):

   ```powershell
   cd backend
   py -3.14 -m venv venv
   .\venv\Scripts\Activate.ps1        # macOS/Linux: source venv/bin/activate
   pip install -r requirements.txt
   copy .env.example .env             # then edit DATABASE_URL, JWT_SECRET_KEY, ...
   flask --app flask_app.app db upgrade
   python -m scripts.seed             # optional demo data
   flask --app flask_app.app run --debug
   ```

   Create the local databases named in `backend/.env.example` (`DATABASE_URL`, `TEST_DATABASE_URL`, `MIGRATION_TEST_DATABASE_URL`, `E2E_DATABASE_URL`) in PostgreSQL first. Never commit `.env` files.

3. Frontend (from `frontend/`, in a second terminal):

   ```powershell
   cd frontend
   npm install
   copy .env.example .env.local       # API_URL=http://localhost:5000
   npm run dev
   ```

The frontend runs on http://localhost:3000 and proxies `/api/*` to the backend at `API_URL`.

Backend variables go in `backend/.env`, and the frontend needs only `API_URL` in `frontend/.env.local`. Never commit either file.

## How to Run the Tests

Backend (from `backend/`, venv active):

```powershell
pytest -v
ruff check . ; ruff format .
mypy .
```

Playwright E2E (from `frontend/`):

```powershell
npm run lint
npm run build
npx playwright install      # first time only, installs the browsers
npx playwright test
npx playwright show-report  # opens the HTML report
```

By default Playwright starts the Flask backend and `npm run dev` itself and points the backend at the dedicated E2E database from `E2E_DATABASE_URL` (default `postgresql+psycopg://taskapp:your_password@localhost:5432/taskmgmt_e2e`, see `frontend/playwright.config.ts`). Set `E2E_DATABASE_URL` in your shell to use another database. Run `flask --app flask_app.app db upgrade` against that database first, with `DATABASE_URL` set to the same value. Tests do not depend on each other's data.

To run the suite against the live Vercel deployment instead, set `E2E_BASE_URL`. No local servers are started in that case, and the tests use the deployed backend and its database. Open `/api/health` first so the free-tier backend is awake.

```powershell
$env:E2E_BASE_URL = "https://task-management-app-red-three.vercel.app"
npx playwright test
npx playwright show-report
```

The frontend has no unit test layer. Frontend behavior is covered by the Playwright suite.

## Deployment

The frontend runs on Vercel, the backend on Render, and the database on Supabase Postgres. Migrations and seeding are run manually from a developer machine against the production `DATABASE_URL` (`flask --app flask_app.app db upgrade`, `python -m scripts.seed`), never at request time. Open `/api/health` before demos to wake the backend. Steps, URLs, and verification results are in [Deployment notes](#deployment-notes).

## Spec-driven workflow

The app was built from specs. In `.kiro/specs/task-management-app/`:
- `requirements.md`: user stories and acceptance criteria
- `design.md`: architecture, data models, API, and correctness properties
- `tasks.md`: the implementation plan
- `CHANGELOG.md`: version history of the spec

Project rules (product, tech, structure, frontend, backend, database, card conventions, workflow) are steering files in `.kiro/steering/`.

## Known limitations

- The free-tier Render backend sleeps when idle. The first request, and a proxied request through Vercel, can be slow or time out while it wakes.
- Supabase Free projects pause after a week of inactivity. Restore the project from the dashboard before demos.
- Writes to archived Boards are not blocked in V1. Only Guest access to an archived Board is rejected.
- p95 < 300 ms (R14.1) and 99.5% availability (R14.2) are design targets, not measured guarantees.
- Dependencies that failed to install in task 1.1: none were recorded (no failure in the task 1.1 commit message, `tasks.md`, or `backend/requirements.txt`).

## Deployment notes

Status: Deployed on 2026-11-16. The checklist below was completed manually from the Supabase, Render and Vercel dashboards. Never write secrets here.

### URLs
- Render backend: `https://backend-task-management-app-cw2q.onrender.com`
- Vercel frontend: `https://task-management-app-red-three.vercel.app`
- Supabase project: `task-management-app` (project name only, no connection string)

### Checklist

1. **Supabase**
   - [x] Create the project with the Data API disabled (plain PostgreSQL).
   - [x] Copy the Session pooler connection string (port 5432) from the Connect dialog.
   - [x] Build `DATABASE_URL` as `postgresql+psycopg://<user>:<url-encoded-password>@<pooler-host>:5432/postgres?sslmode=require`.
2. **Render** (Web Service)
   - [x] Root Directory `backend/`, native Python runtime (no Docker).
   - [x] Build command: `pip install -r requirements.txt`
   - [x] Start command: `gunicorn "flask_app.app:create_app()"` (no `--access-logfile`, so no default-format access log).
   - [x] `PYTHON_VERSION` = fully qualified 3.14 version, e.g. `3.14.3`.
   - [x] Environment variables: `DATABASE_URL`, `JWT_SECRET_KEY` (long random value), `COOKIE_SECURE=true`, `APP_ENV=production` (debug off), `ACCESS_TOKEN_MINUTES=15`, `REFRESH_TOKEN_DAYS=7`.
   - [x] `TEST_DATABASE_URL`, `MIGRATION_TEST_DATABASE_URL` and `E2E_DATABASE_URL` from `backend/.env.example` are for local testing. Set them only if the app needs them to start. They are not set on Render.
3. **Vercel**
   - [x] Root Directory `frontend/`.
   - [x] Server-side env var `API_URL` = Render URL (not `NEXT_PUBLIC_`).
   - [x] Redeploy after any change to `API_URL` (rewrites are read at build time).
4. **Production migration** (from a developer machine, never at request time)
   - [x] In `backend/`, with the production `DATABASE_URL` set in the shell: `flask --app flask_app.app db upgrade`
5. **Verification through the Vercel domain** (open `/api/health` first; the free Render service may be asleep)
   - [x] `curl -i https://<vercel-domain>/api/health` returns 200.
   - [x] Register a test User through the app or `POST /api/auth/register`.
   - [x] `curl -i -X POST https://<vercel-domain>/api/auth/login -H "Content-Type: application/json" -d '{"email":"...","password":"..."}'`
   - [x] Set-Cookie headers: both cookies present, `HttpOnly`, `SameSite=Lax`, `Secure`, no `Domain`; refresh cookie `Path` limited to `/api/auth/refresh` (and `/api/auth/logout`); no tokens in the body.
   - [x] Repeat the login request directly against the Render URL and confirm the Set-Cookie headers are identical.

### Results

| Check | Result |
| --- | --- |
| Health via Vercel | 200 OK |
| Register via Vercel | 201 |
| Production migration (`flask --app flask_app.app db upgrade`) | Ran without errors |
| Login Set-Cookie via Vercel | `access_token` (Path=/, Max-Age=900) and `refresh_token` (Max-Age=604800, Path=/api/auth/refresh, plus a second one with Path=/api/auth/logout). All Secure, HttpOnly, SameSite=Lax, no Domain. Response body has only `displayName`, `email`, `id` (no tokens). |
| Login Set-Cookie direct to Render | Same attributes as via Vercel |
| Headers identical | Yes (only token values and Expires timestamps differ per request, as expected) |

### Commands used

Placeholder credentials only; no token values recorded.

```powershell
curl.exe -i https://task-management-app-red-three.vercel.app/api/health

curl.exe -i -X POST https://task-management-app-red-three.vercel.app/api/auth/register -H "Content-Type: application/json" -d '{\"email\":\"user@example.com\",\"password\":\"<password>\",\"displayName\":\"Test User\"}'

curl.exe -i -X POST https://task-management-app-red-three.vercel.app/api/auth/login -H "Content-Type: application/json" -d '{\"email\":\"user@example.com\",\"password\":\"<password>\"}'

curl.exe -i -X POST https://backend-task-management-app-cw2q.onrender.com/api/auth/login -H "Content-Type: application/json" -d '{\"email\":\"user@example.com\",\"password\":\"<password>\"}'
```

## Screenshots

### Login and Register
![Login](docs/screenshots/login-page.png)
![Register](docs/screenshots/register-page.png)

### Teams
![Teams](docs/screenshots/teams-page.png)

### Board detail with columns and cards
![Board detail](docs/screenshots/boards-detail-page.png)

### Card detail modal with comments
![Card detail modal](docs/screenshots/card-detail-modal.png)

### Profile
![Profile](docs/screenshots/profile-page.png)

### Dragging a card between columns
![Drag and drop](docs/screenshots/drag-and-drop-demo.png)

### Notification bell with an unread count
![Notification bell](docs/screenshots/notification-bell-showing-unread-message.png)

### Playwright HTML report against the live Vercel URL
![Playwright report](docs/screenshots/e2e-playwright-test-on-vercel-url.png)
