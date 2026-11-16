# Task Management App

Trello-inspired task management app. Backend: Flask (`backend/`). Frontend: Next.js (`frontend/`). Specs and steering live in `.kiro/`.

## Deployment notes

Status: Deployed on 2026-11-16. The checklist below was completed manually from the Supabase, Render and Vercel dashboards. Never write secrets here.

### URLs
- Render backend: `https://backend-task-management-app-cw2q.onrender.com`
- Vercel frontend: `https://task-management-app-red-three.vercel.app`
- Supabase project: `task-management-app` (nagement-app` (project name only, no connection string)

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
