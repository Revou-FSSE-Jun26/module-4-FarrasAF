# Implementation Plan: task-management-app

## Overview

Build the project foundation first (Flask backend helpers, then the Next.js scaffold), then the PostgreSQL models and migrations, authentication, a deployed walking skeleton, RBAC, and one backend service module at a time, then the Next.js frontend, then Playwright E2E tests, then documentation, production seed data, and a production smoke test. Each backend module follows `routes.py` + `schema.py` + `service.py` + `__init__.py`, registers its Blueprint in `app.py` in the same task (no orphaned code), and writes Activity_Entries and Notifications in the same transaction as the triggering mutation. Backend code lives in `backend/flask_app/`, frontend code in `frontend/src/`, E2E tests in `frontend/e2e/`.

Implementation language: Python 3.14 (backend) and TypeScript strict mode (frontend), as fixed by `design.md` and `tech.md`.

Conventions applied to every task (see steering `tech`, `structure`, `card-conventions`, `backend`, `database`, `frontend`):
- Route handlers are max 5 lines: `read_json()`/`read_query()` + `load_schema()` + one `*_service` call + `json_response()`.
- Services raise typed errors, run one transaction per route-called function, and never rename fields.
- Every property test lives in `backend/tests/properties/test_property_<n>_<short_name>.py`, uses `hypothesis` with `max_examples=100` minimum, and carries the tag `# Feature: task-management-app, Property {n}: {text}`. Each of the 39 design properties maps to exactly one property test sub-task below.
- Every service function also gets a pytest unit test in `backend/tests/unit/test_<module>.py`.

## Notes

- All tests are required in this project (`tech.md` and `card-conventions.md` rule 5); no task is optional.
- Before each task, read the steering files that match the files being edited (for example `backend.md` for `backend/**/*.py`, `database.md` for models and migrations, `frontend.md` for `frontend/**/*.{ts,tsx}`).
- Never add endpoints, fields, enums, or dependencies that are not in `design.md`.
- Commit after each task with the task number in the message (for example `task 7.1: implement boards module`).
- Do not mark a task complete if its tests fail.
- Each backend module task registers its Blueprint in `app.py`, so no code is left unwired; task 13.1 verifies the full wiring. The Guest Blueprint (`guest_bp`) is registered in task 11.3.
- All 39 correctness properties map to exactly one backend property test sub-task: P1 9.2, P2 10.5, P3 10.6, P4 10.7, P5 7.3, P6 10.3, P7 11.12, P8 10.4, P9 9.3, P10 7.4, P11 11.9, P12 11.8, P13 11.6, P14 11.7, P15 1.4, P16 12.3, P17 12.5, P18 6.2, P19 12.4, P20 11.11, P21 5.2, P22 4.8, P23 8.4, P24 8.5, P25 11.4, P26 4.3, P27 4.4, P28 4.5, P29 4.6, P30 4.7, P31 5.4, P32 7.2, P33 8.3, P34 5.5, P35 10.8, P36 6.3, P37 7.5, P38 7.6, P39 11.10. The same mapping is repeated as a table at the end of this file.
- Properties 31 to 34, 37, and 38 run against the transactional test database with small generators; pure-logic properties run without the database.
- Load/p95 (R14.1) and availability (R14.2) are design targets validated outside this task list; only the health endpoint and responsive layout are implemented and tested here.
- Do not add dependencies outside the `tech.md` stack, Docker, WebSockets, or Supabase client libraries.

## Tasks

- [x] 1. Project foundation: backend helpers and frontend scaffold
  - [x] 1.1 Scaffold the backend project
    - Create `backend/requirements.txt` (pinned versions: Flask, Flask-SQLAlchemy, Flask-Migrate, PyJWT, `psycopg[binary]`, `python-dotenv`, `gunicorn`, `argon2-cffi`, `marshmallow`, plus `pytest`, `hypothesis`, `ruff`, `mypy`), `backend/pyproject.toml` (ruff, mypy, pytest config), `backend/.env.example` (`DATABASE_URL`, `JWT_SECRET_KEY`, `COOKIE_SECURE`, ...)
    - Create a Python 3.14 virtual environment in `backend/venv` (for example `py -3.14 -m venv venv` on Windows), activate it, confirm `python --version` reports 3.14, make sure `venv/` and `.env` are git-ignored, and run `pip install -r requirements.txt` to install every dependency listed in `requirements.txt`
    - Record any dependency that fails to install (package, pinned version, and the error) in the task's commit message and in the README "Known limitations" section (task 20.1); do not silently drop it, substitute another package, or add a dependency outside the `tech.md` stack
    - Create `flask_app/__init__.py`, `config.py` (all env settings, fail fast on missing required values, debug off in production), `extensions.py` (SQLAlchemy `db`, `migrate`, metadata `naming_convention`), and `app.py` with the `create_app()` factory
    - Create empty `tests/{unit,properties,integration}` folders and `scripts/__init__.py`
    - _Requirements: 14.2_

  - [x] 1.2 Implement shared `common/` helpers and central error handling
    - `exceptions.py`: `AppError` subclasses (`ValidationError`, `NotFoundError`, `ConflictError`, `AuthorizationError`, `AuthenticationError`) with snake_case `code` constants including `internal_error`
    - `time.py` (`utc_now`), `pagination.py` (Notifications 50, Activity 100, Search 100), `validation.py` (`BaseSchema` with `unknown = RAISE`, `TrimmedStr`, `NonBlankStr`, `load_schema` reporting the first failing field), `serialization.py` (`read_json`, `read_query`, `json_response`: camelCase/snake_case conversion for keys only, UUID strings, ISO 8601 UTC with `Z`)
    - `health.py`: public `GET /api/health` returning 200 and never touching the database
    - In `app.py`: register the health Blueprint, map `AppError` subclasses and Werkzeug `HTTPException`s to `{ "error": { "code", "message", "field?" } }`, map unexpected exceptions to 500 `internal_error` after logging the traceback, and roll back the session in every handler
    - _Requirements: 13.5, 14.2, 15.3, 15.5_

  - [x] 1.3 Implement pure ordering and cursor logic
    - `common/ordering.py`: side-effect-free `reindex(items)` assigning contiguous `order_index` `0..n-1` (adds to the session only, never commits)
    - `common/cursor.py`: `encode_cursor(created_at, id)` / `decode_cursor(token)` producing an opaque URL-safe string and raising `ValidationError` on malformed input
    - _Requirements: 2.3, 2.5, 3.5, 4.2, 6.7, 6.10_

  - [x] 1.4 Write property test for the cursor codec
    - File: `tests/properties/test_property_15_cursor_codec.py`
    - **Property 15: Notification cursor codec round-trip**
    - **Validates: Requirements 6.10**

  - [x] 1.5 Write unit tests for common helpers
    - `tests/unit/test_common.py`: camelCase/snake_case conversion, `TrimmedStr`/`NonBlankStr`/`load_schema` behavior, error-to-envelope mapping (including 404/405/500), `reindex` examples, and that `/api/health` returns 200 without a database session
    - _Requirements: 6.10, 14.2_

  - [x] 1.6 Scaffold the Next.js app
    - Create `frontend/` with Next.js App Router, React, TypeScript strict mode (alias `@/*` -> `./src/*`), Tailwind CSS, `eslint`, `prettier` with `prettier-plugin-tailwindcss`, `.env.example` (`API_URL`), `playwright.config.ts`, and `next.config.ts` with the `/api/:path*` rewrite to `API_URL` and `Referrer-Policy: no-referrer` headers for `/invite/:token*` and `/join/:token*`
    - ESLint config keeps `@typescript-eslint/no-explicit-any` set to `error`
    - `playwright.config.ts` defines a `webServer` array that starts both servers: the Flask backend (started with the venv's Python executable, `python -m flask --app flask_app.app run` from `backend/`, for example `venv/Scripts/python` on Windows and `venv/bin/python` elsewhere, so the E2E run does not depend on a shell with the venv activated) and the frontend (`npm run dev` from `frontend/`), each with a `url` readiness check (`/api/health` for the backend) and `reuseExistingServer` outside CI; the backend gets `DATABASE_URL` pointing to a dedicated E2E test database (never the development or production database), `JWT_SECRET_KEY`, and `COOKIE_SECURE=false`, and the frontend gets `API_URL` pointing to that local backend; `baseURL` is the local frontend
    - All application code under `src/`; install `@dnd-kit/core` and `@dnd-kit/sortable` with pinned versions
    - _Requirements: 14.3, 14.4, 11.3, 17.3_

- [x] 2. Data models and migrations
  - [x] 2.1 Create `BaseModel` and identity/team models
    - `models/base.py`: `BaseModel` with exactly `id` (UUID v4), `created_at`, `updated_at`, `deleted_at`
    - Models: `User` (email unique lowercased, `password_hash`, `display_name`, `failed_login_attempts`, `locked_until`), `RefreshToken` (`token_hash` unique, `expires_at`, `revoked`), `Team`, `TeamMembership` (`team_role` check constraint, unique `(team_id, user_id)`), `TeamJoinLink` (`token` unique, `status`, `expires_at`, `created_by_id`)
    - Enum-like values as `String(50)` + `CheckConstraint`; relationships on both sides with explicit `lazy`
    - _Requirements: 15.1, 15.4, 15.8, 15.14, 15.15, 16.1, 17.1_

  - [x] 2.2 Create Board-domain models
    - Models: `Board`, `BoardMembership` (unique `(board_id, user_id)`), `Column` (deferrable unique `(board_id, order_index)`), `Card` (own `updated_at` with `default=utc_now` and no `onupdate`, `version`, deferrable unique `(column_id, order_index)`, indexes from `design.md`), `Comment` (self-referential `parent_comment_id`, `edited_at`, `version`), `Notification` (unique `(recipient_id, comment_id)`, cursor and unread partial indexes), `InvitationLink`, `ActivityEntry` (no FK on `resource_id`, index `(board_id, created_at desc, id desc)`)
    - Board-delete cascades via `ondelete="CASCADE"` and `passive_deletes=True`; `models/__init__.py` imports every model so Alembic sees them
    - _Requirements: 1.6, 2.1, 3.1, 4.7, 5.2, 6.1, 8.12, 11.1, 13.4_

  - [x] 2.3 Create and review migration (a): identity and Team tables
    - Tables: `users`, `refresh_tokens`, `teams`, `team_memberships`, `team_join_links` (models `User`, `RefreshToken`, `Team`, `TeamMembership`, `TeamJoinLink`)
    - Generate with `flask --app flask_app.app db migrate -m "identity and team tables"`; if autogenerate emits all tables at once, split the output into three revision files (a), (b), (c) by table group before any is applied, and chain `down_revision` (a) -> (b) -> (c)
    - Hand-review for `CheckConstraint`, unique constraints, indexes, and naming-convention names; ensure a working `downgrade`; verify `upgrade` then `downgrade` on the local database
    - Run `flask --app flask_app.app db init` once to create `migrations/` and commit it; confirm `migrations/env.py` uses the app's metadata (including the `naming_convention`) so autogenerate sees every model
    - _Requirements: 15.1, 15.8, 16.1, 17.1_

  - [x] 2.4 Create and review migration (b): Board, Column, Card, and access tables
    - Tables: `boards`, `board_memberships`, `columns`, `cards`, `invitation_links` (models `Board`, `BoardMembership`, `Column`, `Card`, `InvitationLink`); depends on migration (a)
    - Hand-review for the deferrable `INITIALLY DEFERRED` unique constraints on `(board_id, order_index)` and `(column_id, order_index)`, the Card indexes from `design.md`, `ondelete="CASCADE"` on Board children, and a Card `updated_at` with no server-side update trigger; ensure a working `downgrade`
    - _Requirements: 1.6, 2.3, 4.2, 4.7, 11.1_

  - [x] 2.5 Create and review migration (c): Comment, Notification, and Activity tables
    - Tables: `comments`, `notifications`, `activity_entries` (models `Comment`, `Notification`, `ActivityEntry`); depends on migration (b)
    - Hand-review for the self-referential `parent_comment_id`, the unique `(recipient_id, comment_id)`, the Notification cursor and unread partial indexes, the `(board_id, created_at desc, id desc)` Activity index, no FK on `resource_id`, and Board-delete cascades; ensure a working `downgrade`; run `upgrade head` and `downgrade base` end to end
    - _Requirements: 1.6, 5.2, 6.1, 8.12_

  - [x] 2.6 Create the test database fixtures
    - `tests/conftest.py`: app fixture, transactional DB session with rollback per test, factory fixtures for users, teams, boards, columns, cards, and a controllable clock for `utc_now`
    - _Requirements: 15.7_

  - [x] 2.7 Write schema verification tests
    - File: `tests/integration/test_schema_constraints.py`, run against PostgreSQL
    - A multi-row `order_index` reindex (for example swapping or shifting several Cards in one Column, and several Columns in one Board) succeeds inside one transaction with the deferrable unique constraints, and a genuine duplicate still fails at commit
    - An unrelated `UPDATE` (for example on a Card's `description`, or reindexing a different Card) does not change a Card's `updated_at`
    - `db.Uuid` columns work through an Alembic `upgrade` and `downgrade` on PostgreSQL (run in a separate migration-test database, outside the transactional rollback fixture, and check the column type is `uuid`)
    - `with_for_update()` works (row lock acquired on Column rows; a second session blocks or uses `nowait`/`skip_locked` to prove the lock)
    - `TrimmedStr` trims before the length check (for example `"  a  "` passes a `min=1, max=1` validator and `"   "` fails `min=1`)
    - _Requirements: 2.3, 4.2, 4.7_

- [ ] 3. Checkpoint - Ensure all tests pass
  - [-] 3.1 Run all checks and commit
    - Backend (from `backend/`, venv active): `pytest`, `ruff check .`, `ruff format --check .`, `mypy .`
    - Frontend (from `frontend/`): `npm run lint`, `npm run build`, `npx playwright test` (skip while no E2E specs exist)
    - Fix every failure, ask the user if questions arise, then commit with the checkpoint number in the message

- [ ] 4. Authentication_Service
  - [ ] 4.1 Implement the `auth/` module
    - `service.py`: register (account only, argon2 hash, duplicate email is a `ValidationError`), login (generic error, lockout after 3 consecutive failures for 15 minutes via `utc_now()`, counter reset on success and after the window), refresh (valid, non-revoked, non-expired token yields identity-only access token), logout (revoke refresh token), `me`
    - `schema.py` (email format, password >= 8 and never trimmed, `display_name` 1-50 trimmed), `routes.py` (public register/login/refresh/logout, `GET /api/auth/me`), `set_auth_cookies()` / `clear_auth_cookies()` (`HttpOnly`, `SameSite=Lax`, no `Domain`, `Secure` from `COOKIE_SECURE`, refresh cookie scoped to `/api/auth/refresh` and `/api/auth/logout`), `@token_required` decorator, refresh tokens stored hashed from `secrets.token_urlsafe`
    - Register the Blueprint in `app.py`; never return tokens in bodies or log them
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8, 15.9, 15.10, 15.11, 15.12, 15.13, 15.14, 15.15, 15.16_

  - [ ] 4.2 Write unit tests for the auth service
    - `tests/unit/test_auth.py`: login sets both cookies and returns identity (R15.2), logout revokes refresh token and clears cookies (R15.8), refresh issues a new identity-only token (R15.11), duplicate email (R15.15), lockout lock/unlock with the controllable clock (R15.4-15.7)
    - _Requirements: 15.2, 15.4, 15.5, 15.6, 15.7, 15.8, 15.11, 15.15_

  - [ ] 4.3 Write property test for password hashing
    - File: `tests/properties/test_property_26_password_hash.py`
    - **Property 26: Passwords are stored as a verifiable argon2 hash**
    - **Validates: Requirements 15.1**

  - [ ] 4.4 Write property test for generic login failures
    - File: `tests/properties/test_property_27_generic_login_error.py`
    - **Property 27: Login failures do not disclose which field was wrong**
    - **Validates: Requirements 15.3**

  - [ ] 4.5 Write property test for registration validation
    - File: `tests/properties/test_property_28_registration_validation.py`
    - **Property 28: Registration validation enforces email format, password length, uniqueness, and display name**
    - **Validates: Requirements 15.14, 15.15, 15.16**

  - [ ] 4.6 Write property test for refresh-token exchange and revocation
    - File: `tests/properties/test_property_29_refresh_token.py`
    - **Property 29: Refresh-token exchange and revocation**
    - **Validates: Requirements 15.8, 15.11, 15.12, 15.13**

  - [ ] 4.7 Write property test for account lockout
    - File: `tests/properties/test_property_30_account_lockout.py`
    - **Property 30: Account lockout after three consecutive failed logins**
    - **Validates: Requirements 15.4, 15.5, 15.6, 15.7**

  - [ ] 4.8 Write property test for the authentication gate
    - File: `tests/properties/test_property_22_auth_gate.py`
    - **Property 22: Authentication gate precedes authorization**
    - **Validates: Requirements 12.6, 15.9, 15.10**

  - [ ] 4.9 Deploy the walking skeleton
    - Supabase: create the project with the Data API disabled (used only as plain PostgreSQL); copy the Session pooler connection string (port 5432), use the `postgresql+psycopg://` scheme with `sslmode=require`, and URL-encode special characters in the password
    - Render: create the Web Service with Root Directory `backend/`, native Python runtime (no Docker), build command `pip install -r requirements.txt`, start command `gunicorn "flask_app.app:create_app()"` (no default-format access log), `PYTHON_VERSION` set to a fully qualified 3.14 version (for example `3.14.3`), and environment variables `DATABASE_URL`, `JWT_SECRET_KEY`, `COOKIE_SECURE=true`, plus every other variable in `backend/.env.example`; debug off
    - Vercel: create the project with Root Directory `frontend/` and the server-side `API_URL` environment variable (not `NEXT_PUBLIC_`) pointing to the Render URL; the rewrites in `next.config.ts` are read at build time, so after changing `API_URL` the Vercel project must be redeployed
    - Run the production migration from a developer machine against the production `DATABASE_URL`: `flask --app flask_app.app db upgrade` (never at request time)
    - Verify through the Vercel domain (open `/api/health` first to wake the free-tier backend): `curl -i https://<vercel-domain>/api/health` returns 200; register a test User, then `curl -i -X POST https://<vercel-domain>/api/auth/login` with that User and confirm the `Set-Cookie` headers arrive unchanged (both cookies present, `HttpOnly`, `SameSite=Lax`, `Secure`, no `Domain`, refresh cookie `Path` limited to `/api/auth/refresh`, and tokens absent from the body) by comparing with the same request sent straight to the Render URL
    - Create the root `README.md` if it does not exist yet and record the URLs (without secrets), the commands used, and the results under a "Deployment notes" heading
    - _Requirements: 14.2, 15.2_

- [ ] 5. RBAC and Team_Service
  - [ ] 5.1 Implement RBAC in `access/rbac.py`
    - Pure role-decision function (role + operation -> allow/deny) matching the capability matrix, and `@require_role('member' | 'admin')` that runs the authentication check first, resolves the Board from route parameters, and reads the role from stored `BoardMembership` (never the token)
    - `current_user()` helper; missing role raises `AuthorizationError`
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

  - [ ] 5.2 Write property test for RBAC decisions
    - File: `tests/properties/test_property_21_rbac_matrix.py`
    - **Property 21: RBAC authorization decisions match the role capability matrix**
    - **Validates: Requirements 1.7, 2.8, 3.6, 4.6, 5.6, 8.14, 10.7, 11.4, 11.7, 12.1, 12.2, 12.3, 12.4, 12.5**

  - [ ] 5.3 Implement the `teams/` module
    - `service.py`: create Team (creator becomes `team_admin`), list caller's Teams with `current_user_team_role`, list members (Team members only), generate/list/revoke Team_Join_Links (Team_Admin only, 7-day expiry, `is_expired` derived at read time), preview (generic invalid-link `ValidationError`), accept (single transaction, `team_regular`, already-member rejected)
    - `schema.py`, `routes.py` per the Team_Service endpoint table (all with `@token_required`); Team_Role read from stored `TeamMembership` on every request; register Blueprint in `app.py`
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 17.8, 17.9_

  - [ ] 5.4 Write property test for Teams
    - File: `tests/properties/test_property_31_teams.py`
    - **Property 31: Team creation, listing, membership, and access control**
    - **Validates: Requirements 16.1, 16.2, 16.3, 16.4, 16.5**

  - [ ] 5.5 Write property test for Team_Join_Link lifecycle
    - File: `tests/properties/test_property_34_team_join_link.py`
    - **Property 34: Team_Join_Link lifecycle and access control**
    - **Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7**

  - [ ] 5.6 Write unit tests for the teams service
    - `tests/unit/test_teams.py`: creator is `team_admin`, join-link accept, expired link (R17.4), non-member members request (R16.5), preview returns only the Team name (R17.8), list shape (R17.9)
    - _Requirements: 16.1, 16.5, 17.3, 17.4, 17.8, 17.9_

- [ ] 6. Activity_Service
  - [ ] 6.1 Implement the `activity/` module
    - `service.py`: `record_activity()` helper (adds to the session, never commits) for all eleven event types; paged read ordered `created_at DESC, id DESC`, 100 per page, zero-based page, negative or out-of-range page gives an empty page
    - `schema.py` (`page` strict integer), `routes.py` `GET /api/boards/{boardId}/activity` with `@require_role('member')`, response `{ items, page, pageSize }`; register Blueprint in `app.py`
    - _Requirements: 8.1, 8.12, 8.13, 8.14, 8.15_

  - [ ] 6.2 Write property test for Activity pagination
    - File: `tests/properties/test_property_18_activity_pagination.py`
    - **Property 18: Activity pagination visits each entry exactly once in order**
    - **Validates: Requirements 8.12, 8.15**

  - [ ] 6.3 Write property test for Activity access
    - File: `tests/properties/test_property_36_activity_access.py`
    - **Property 36: Activity is readable only by Members and Admins**
    - **Validates: Requirements 8.14**

- [ ] 7. Board_Service
  - [ ] 7.1 Implement the `boards/` module
    - `service.py`: create (Board + creator Admin `BoardMembership` + default Columns "To Do", "Doing", "Done" at 0, 1, 2 in one transaction; requester must be a Team_Member), list (caller's Boards, active by default, archived filter only for Admin Boards), get with `current_user_role`, atomic partial update (`name`, `description`, `visibility`), archive, restore (non-archived is a `ValidationError`), permanent delete with cascade
    - `schema.py`, `routes.py` per the Board_Service endpoint table (`visibility` stored with no access effect); register Blueprint in `app.py`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 1.12, 1.13, 1.14_

  - [ ] 7.2 Write property test for Board creation
    - File: `tests/properties/test_property_32_board_creation.py`
    - **Property 32: Board creation grants the creator Admin effective immediately**
    - **Validates: Requirements 1.1, 1.11, 1.12**

  - [ ] 7.3 Write property test for Board partial updates
    - File: `tests/properties/test_property_05_board_partial_update.py`
    - **Property 5: Board partial update preserves omitted fields; invalid field rejects atomically**
    - **Validates: Requirements 1.3, 1.10**

  - [ ] 7.4 Write property test for Board cascade delete
    - File: `tests/properties/test_property_10_board_cascade_delete.py`
    - **Property 10: Board permanent delete cascades completely**
    - **Validates: Requirements 1.6**

  - [ ] 7.5 Write property test for the Board list
    - File: `tests/properties/test_property_37_board_list.py`
    - **Property 37: Board list reflects the caller's Board roles and the archived filter**
    - **Validates: Requirements 1.13**

  - [ ] 7.6 Write property test for visibility
    - File: `tests/properties/test_property_38_visibility_no_effect.py`
    - **Property 38: Visibility does not change who can access a Board**
    - **Validates: Requirements 1.14**

  - [ ] 7.7 Write unit tests for the boards service
    - `tests/unit/test_boards.py`: default columns (R1.2), archive/restore (R1.4, R1.5), restore of a non-archived Board (R1.9), non-Admin rejection (R1.7), invalid name (R1.8)
    - _Requirements: 1.2, 1.4, 1.5, 1.7, 1.8, 1.9_

- [ ] 8. Access_Control_Service: members and invitations
  - [ ] 8.1 Implement Board member management in `access/`
    - `service.py`: list members, add member (`user_id` must be a Team_Member of the Board's Team, role `member`/`admin`, not already a member), change role, remove member (never leaving zero Admins); record `member_joined` / `member_removed` via `record_activity()` in the same transaction
    - `schema.py`, `routes.py` (`access_bp`) per the members endpoint table; roles read from stored membership so changes apply on the next request; register Blueprint in `app.py`
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9, 8.10, 8.11_

  - [ ] 8.2 Implement Invitation_Link generate, list, and revoke
    - `service.py`: generate (`secrets.token_urlsafe`), list, revoke (only that link becomes inactive; Admin only)
    - `routes.py`: invitation routes on `access_bp` with `@require_role('admin')`; register in `app.py`. The anonymous Guest routes and token resolution are implemented in task 11.3, after Comments exist
    - _Requirements: 11.1, 11.2, 11.7, 11.9_

  - [ ] 8.3 Write property test for Board invitations
    - File: `tests/properties/test_property_33_board_invitations.py`
    - **Property 33: Board invitations require an eligible, not-already-member Team_Member**
    - **Validates: Requirements 10.1, 10.4, 10.5, 10.8**

  - [ ] 8.4 Write property test for the last-Admin invariant
    - File: `tests/properties/test_property_23_last_admin.py`
    - **Property 23: Board retains at least one Admin**
    - **Validates: Requirements 10.6**

  - [ ] 8.5 Write property test for role changes applying on the next request
    - File: `tests/properties/test_property_24_role_change_next_request.py`
    - **Property 24: Role changes apply on the next request from stored membership**
    - **Validates: Requirements 10.2, 10.3**

  - [ ] 8.6 Write unit tests for members and invitations
    - `tests/unit/test_access.py`: non-Admin rejection (R10.7, R11.7), members list shape (R10.9), invitation list shape (R11.9), generate and revoke affect only the targeted link (R11.1, R11.2). Guest-route unit tests are in task 11.5
    - _Requirements: 10.7, 10.9, 11.1, 11.2, 11.7, 11.9_

- [ ] 9. Column_Service
  - [ ] 9.1 Implement the `columns/` module
    - `service.py`: create (append at end), rename, reorder (target index validated to `0..n-1`, contiguous reindex), delete (empty only, then reindex); lock the Board's Column rows with `with_for_update()` before reindexing; record `column_created` / `column_deleted` in the same transaction
    - `schema.py`, `routes.py` with `@require_role('admin')` per the Column_Service table; register Blueprint in `app.py`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 8.8, 8.9_

  - [ ] 9.2 Write property test for Column ordering
    - File: `tests/properties/test_property_01_column_ordering.py`
    - **Property 1: Column ordering is always contiguous from zero**
    - **Validates: Requirements 2.1, 2.3, 2.5**

  - [ ] 9.3 Write property test for non-empty Column deletion
    - File: `tests/properties/test_property_09_nonempty_column_delete.py`
    - **Property 9: Non-empty column cannot be deleted**
    - **Validates: Requirements 2.4**

  - [ ] 9.4 Write unit tests for the columns service
    - `tests/unit/test_columns.py`: append index, rename, invalid name (R2.6), out-of-range reorder (R2.7), non-Admin rejection (R2.8), activity entries recorded
    - _Requirements: 2.1, 2.2, 2.6, 2.7, 2.8, 8.8, 8.9_

- [ ] 10. Card_Service
  - [ ] 10.1 Implement Card create, read, edit, and delete
    - `service.py`: create (append at end, `version = 1`, `created_at == updated_at`), get (includes `version`), PATCH (atomic multi-field validation first; Assignee must be a current Board Member; conditional `UPDATE ... WHERE version = :expected`; missing `version` raises `ConflictError`; sets `updated_at` explicitly and increments `version`), delete (no `version` required, reindex column); record `card_created` / `card_updated` / `card_deleted` in the same transaction
    - `schema.py` (`version` never `required`, strict int when present), `routes.py` per the Card_Service table; register Blueprint in `app.py`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 8.1, 8.2, 8.5_

  - [ ] 10.2 Implement Card move and reorder
    - `move_card_service(card_id, target_column_id, target_index, actor)`: target Column must belong to the same Board, target index an integer in `[0, count-in-target-after-removal]`; lock affected Column rows with `with_for_update()`, `reindex()` source and target, set `updated_at` only on the moved Card, never change `version`, record `card_moved` once, commit once
    - Add schema and the `POST /api/cards/{cardId}/move` route (no `version`)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 13.6, 8.3_

  - [ ] 10.3 Write property test for atomic Card edits
    - File: `tests/properties/test_property_06_card_edit_atomic.py`
    - **Property 6: Card edit is atomic across multiple fields**
    - **Validates: Requirements 3.3, 3.10**

  - [ ] 10.4 Write property test for Assignee membership
    - File: `tests/properties/test_property_08_assignee_membership.py`
    - **Property 8: Assignment requires board membership**
    - **Validates: Requirements 3.4, 3.8**

  - [ ] 10.5 Write property test for Card ordering
    - File: `tests/properties/test_property_02_card_ordering.py`
    - **Property 2: Card ordering is always contiguous from zero**
    - **Validates: Requirements 3.2, 3.5, 4.1, 4.2**

  - [ ] 10.6 Write property test for position persistence
    - File: `tests/properties/test_property_03_card_position_roundtrip.py`
    - **Property 3: Card position round-trip persistence**
    - **Validates: Requirements 4.3**

  - [ ] 10.7 Write property test for invalid moves
    - File: `tests/properties/test_property_04_invalid_move_unchanged.py`
    - **Property 4: Out-of-range or cross-board moves leave position unchanged**
    - **Validates: Requirements 2.7, 4.4, 4.5**

  - [ ] 10.8 Write property test for move timestamps and version
    - File: `tests/properties/test_property_35_move_updated_at_version.py`
    - **Property 35: Card move changes only the moved Card's updated_at and never its version**
    - **Validates: Requirements 4.7, 13.6**

  - [ ] 10.9 Write unit tests for the cards service
    - `tests/unit/test_cards.py`: append-to-end (see `card-conventions.md` rule 5), not-found (R3.9), Guest rejection with three cases (a non-GET request to `/api/guest/<token>/...` returns 403 `AuthorizationError`; an authenticated User with no role on the Board returns 403 `AuthorizationError`; a request without cookies to an authenticated route returns 401 `AuthenticationError`, since Guests are anonymous) (R3.6, R4.6), `version` returned on read and set to 1 on create, activity entries recorded
    - _Requirements: 3.1, 3.2, 3.6, 3.9, 4.6, 13.1, 13.4_

- [ ] 11. Notification_Service, Comment_Service, and Guest routes
  - [ ] 11.1 Implement the `notifications/` module
    - `service.py`: `create_mention_notifications()` helper (adds only; one unread Notification per distinct mentioned current Board Member), cursor-paginated list (50 per page, `created_at DESC, id DESC`, `unread_only` filter, `{ items, nextCursor }`), mark as read (recipient only, else `AuthorizationError`)
    - `schema.py` (`cursor`, `unread_only`), `routes.py` with `@token_required`; malformed cursor gives `ValidationError` and no items; register Blueprint in `app.py`
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10_

  - [ ] 11.2 Implement the `comments/` module with mentions
    - `service.py`: pure mention parser extracting distinct valid UUIDs from `@[<uuid>]` tokens; create top-level and reply (parent must exist on the same Card), list as a flat oldest-first list with `parent_comment_id`, edit (author only, `version` required, conditional `UPDATE` sets `edited_at` and increments `version`), delete (author only, cascades to the reply subtree, no `version`); create runs the parser, creates Notifications and the `comment_created` Activity_Entry in the same transaction and never rejects a Comment for an invalid mention; record `comment_edited` / `comment_deleted`
    - `schema.py` (`NonBlankStr`, max 5000), `routes.py` per the Comment_Service table; register Blueprint in `app.py`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 6.1, 6.8, 13.1, 13.2, 13.3, 13.5, 13.6, 8.4, 8.6, 8.7_

  - [ ] 11.3 Implement the anonymous Guest routes
    - `access/service.py`: one function resolving a token to its Board (unknown, inactive, revoked, or archived-Board token raises `AuthorizationError`; Card outside the Board raises `NotFoundError`); Guest read functions reuse the Comment list from task 11.2
    - `access/routes.py`: `guest_bp` with `GET /api/guest/<token>/board` and `GET /api/guest/<token>/cards/<uuid:card_id>/comments`, no authentication, responses expose Users only as `{ id, displayName }` and never emails, `version`, or Activity; any non-GET method on `/api/guest/` returns 403 `AuthorizationError`; register `guest_bp` in `app.py`; Invitation_Link generate, list, and revoke stay in task 8.2
    - _Requirements: 11.3, 11.4, 11.5, 11.6, 11.8_

  - [ ] 11.4 Write property test for invitation links and Guest access
    - File: `tests/properties/test_property_25_invitation_guest_access.py`
    - **Property 25: Invitation link generation, isolation, and anonymous Guest access control**
    - **Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.8**

  - [ ] 11.5 Write unit tests for Guest routes
    - `tests/unit/test_guest.py`: unknown token (R11.6), Guest rejection with three cases (a non-GET request to `/api/guest/<token>/...` returns 403 `AuthorizationError` (R11.4); an authenticated User with no role on the Board returns 403 `AuthorizationError`; a request without cookies to an authenticated route returns 401 `AuthenticationError`, since Guests are anonymous), Guest payload has no emails, `version`, or Activity (R11.3), archived-Board token rejected (R11.8), Card outside the token's Board returns not-found
    - _Requirements: 11.3, 11.4, 11.6, 11.8_

  - [ ] 11.6 Write property test for mention notifications
    - File: `tests/properties/test_property_13_mention_notifications.py`
    - **Property 13: Mentions create exactly one unread notification per distinct board member**
    - **Validates: Requirements 6.1, 6.8**

  - [ ] 11.7 Write property test for Notification pagination
    - File: `tests/properties/test_property_14_notification_pagination.py`
    - **Property 14: Notification cursor pagination visits each notification exactly once in order**
    - **Validates: Requirements 6.2, 6.3, 6.4, 6.6, 6.7**

  - [ ] 11.8 Write property test for reply threading
    - File: `tests/properties/test_property_12_reply_threading.py`
    - **Property 12: Reply threading validity**
    - **Validates: Requirements 5.2, 5.8**

  - [ ] 11.9 Write property test for Comment subtree deletion
    - File: `tests/properties/test_property_11_comment_subtree_delete.py`
    - **Property 11: Comment deletion removes the entire reply subtree**
    - **Validates: Requirements 5.4**

  - [ ] 11.10 Write property test for Comment ownership
    - File: `tests/properties/test_property_39_comment_ownership.py`
    - **Property 39: Only the author can edit or delete a Comment**
    - **Validates: Requirements 5.5**

  - [ ] 11.11 Write property test for optimistic concurrency
    - File: `tests/properties/test_property_20_optimistic_concurrency.py`
    - **Property 20: Optimistic concurrency prevents silent overwrites**
    - **Validates: Requirements 13.2, 13.3, 13.5, 14.5**

  - [ ] 11.12 Write property test for input validation
    - File: `tests/properties/test_property_07_input_validation.py`
    - **Property 7: Input validation rejects invalid values and leaves state unchanged**
    - **Validates: Requirements 1.8, 2.6, 3.7, 5.7**

  - [ ] 11.13 Write unit tests for notifications and comments
    - `tests/unit/test_notifications.py` and `tests/unit/test_comments.py`: mark-as-read (R6.5), marking another user's Notification (R6.9), malformed cursor (R6.10), mention parser examples (duplicates, invalid ids, non-members), Guest rejection (R5.6) with three cases (a non-GET request to `/api/guest/<token>/...` returns 403 `AuthorizationError`; an authenticated User with no role on the Board returns 403 `AuthorizationError`; a request without cookies to an authenticated route returns 401 `AuthenticationError`, since Guests are anonymous)
    - _Requirements: 5.6, 6.5, 6.9, 6.10_

- [ ] 12. Search_Service and Analytics_Service
  - [ ] 12.1 Implement the `search/` module
    - `service.py`: keyword 1-100 non-blank chars, escape `%`, `_`, `\` before a case-insensitive `ILIKE`, restrict to accessible Boards, include Board and Column per result, order `updated_at DESC, id DESC`, cap 100, eager-load to avoid N+1
    - `schema.py` (`q`), `routes.py` `GET /api/search/cards` with `@token_required`; register Blueprint in `app.py`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

  - [ ] 12.2 Implement the `analytics/` module
    - `service.py`: `totalCards`, `perColumn`, `completionRate` (sum over all Columns named exactly "Done" divided by total; 0 when no cards or no "Done" column), `activityByDay` grouped by UTC day; pure completion-rate function kept side-effect-free
    - `routes.py` `GET /api/boards/{boardId}/analytics` with `@require_role('member')`; no `schema.py` (no body or query); register Blueprint in `app.py`
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [ ] 12.3 Write property test for search
    - File: `tests/properties/test_property_16_search.py`
    - **Property 16: Search result soundness, completeness, content, ordering, and cap**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.6**

  - [ ] 12.4 Write property test for analytics
    - File: `tests/properties/test_property_19_analytics.py`
    - **Property 19: Analytics counts and completion rate are consistent and bounded**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6**

  - [ ] 12.5 Write property test for Activity recording
    - File: `tests/properties/test_property_17_activity_recording.py`
    - **Property 17: Activity entries are recorded faithfully for each tracked event**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 8.11, 8.13**

- [ ] 13. Backend integration and seed data
  - [ ] 13.1 Finalize app wiring, logging, and the seed script
    - Verify every Blueprint is registered in `app.py`; add request logging by route template only (`request.url_rule.rule` or `unmatched`, method, status, user id; never raw path, query, cookies, bodies, tokens, or Comment text)
    - `scripts/seed.py` (run with `python -m scripts.seed`): idempotent demo and E2E data (users, a Team with a Team_Admin and a regular member, a Board with default Columns and Cards, a Comment thread, an active Invitation_Link)
    - _Requirements: 1.2, 11.1, 12.6, 14.2_

  - [ ] 13.2 Write backend integration tests
    - `tests/integration/test_api_flows.py`: end-to-end API flows through the authentication and RBAC gates (401 before 403, Guest read-only, role change on the next request), concurrent Card edits with no lost update (R14.5), and the lockout flow
    - _Requirements: 12.6, 14.5, 15.4, 15.5_

- [ ] 14. Checkpoint - Ensure all backend tests pass
  - [ ] 14.1 Run all checks and commit
    - Backend (from `backend/`, venv active): `pytest`, `ruff check .`, `ruff format --check .`, `mypy .`
    - Frontend (from `frontend/`): `npm run lint`, `npm run build`, `npx playwright test` (skip while no E2E specs exist)
    - Fix every failure, ask the user if questions arise, then commit with the checkpoint number in the message

- [ ] 15. Frontend foundation
  - [ ] 15.1 Create API types and the typed API client
    - `src/types/api.ts`: camelCase types for every response shape in the design's API Response Schemas (User, Team, TeamMember, TeamJoinLink, TeamJoinLinkPreview, Board without `updatedAt`, BoardMember, Column, Card, Comment, Notification, ActivityEntry, InvitationLink, Analytics, Guest shapes, paginated responses, error envelope) plus request types; no `any`
    - `src/lib/apiClient.ts`: one typed method per backend endpoint (all later frontend tasks reuse it), same-origin `/api/...` only, no token handling or storage, one refresh-and-retry on `401` (redirect to `/login` except on `/login`, `/register`, `/invite/[token]`; `/join/[token]` returns to the same link after login), no JSON parsing for `204`
    - _Requirements: 15.2, 15.10, 15.11, 15.12, 13.2_

  - [ ] 15.2 Create shared primitives and state components
    - `src/components/shared/`: `BaseButton`, `BaseInput`, `BaseModal`, `BaseToast`, and loading, empty, and error state components
    - _Requirements: 14.3, 14.4_

  - [ ] 15.3 Implement authentication UI and the app shell
    - `useAuth` hook, `/login` and `/register` pages (generic login error, client validation for UX only), authenticated layout with primary navigation linking every route (teams, boards, search) and logout
    - _Requirements: 15.1, 15.2, 15.3, 15.8, 15.9, 15.14, 15.16_

- [ ] 16. Teams UI
  - [ ] 16.1 Implement Teams pages and join flow
    - `useTeams` hook, `/teams` (list and create), `/teams/[teamId]` (members; join-link create, list, revoke shown only when `currentUserTeamRole` is `team_admin`), `/join/[token]` (preview the Team name, call accept only after confirmation, one generic invalid-link message, login redirect and return)
    - Components under `src/components/team/`
    - _Requirements: 16.1, 16.3, 16.4, 17.1, 17.2, 17.3, 17.4, 17.8, 17.9_

- [ ] 17. Boards, Cards, and collaboration UI
  - [ ] 17.1 Implement Board list and settings pages
    - `useBoards` hook, `/boards` (list, create in a chosen Team, archived filter), `/boards/[boardId]/settings` (edit, archive, restore, delete, members and roles, Invitation_Links) with role-aware controls from `currentUserRole`
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 1.6, 1.13, 10.1, 10.3, 10.9, 11.1, 11.2, 11.9_

  - [ ] 17.2 Implement the Board view
    - `useBoard` hook, `/boards/[boardId]` with Columns and Cards, Admin-only Column controls (add, rename, reorder, delete), add Card, loading/empty/error states, responsive layout (`lg:` breakpoint: full board without horizontal scroll at >= 1024px, stacked and usable below)
    - Components under `src/components/board/` and `src/components/card/`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 14.3, 14.4_

  - [ ] 17.3 Implement drag-and-drop
    - Pure helper in `src/lib/` computing target Column id and target index; `useDragAndDrop` hook using `@dnd-kit/core` and `@dnd-kit/sortable` with optimistic reorder, reconciliation with the server response, and rollback with an error message on failure; Guests and non-writers cannot drag
    - _Requirements: 4.1, 4.2, 4.3, 4.6_

  - [ ] 17.4 Implement the Card detail modal
    - Edit Title, Description, Assignee (Board members), Due date; send `version` on every edit and on a `409` refetch and inform the user; delete Card
    - _Requirements: 3.3, 3.4, 3.5, 13.1, 13.2, 13.5_

  - [ ] 17.5 Implement Comments and Mentions
    - `useComments` hook, flat list built into a thread tree in the client from `parentCommentId`, reply, edit (own, with `version`), delete (own), mention picker inserting `@[<userId>]` from the Board members list, tokens rendered as plain-text `@displayName` (or `@unknown`); no `dangerouslySetInnerHTML`
    - Components under `src/components/comment/`, integrated into the Card detail modal
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 13.2_

  - [ ] 17.6 Implement the Notification bell
    - `useNotifications` polling the newest page without a cursor on an interval; "Load more" uses `nextCursor` for older pages; unread-only filter; mark as read; integrated into the app shell
    - Components under `src/components/notification/`
    - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6_

  - [ ] 17.7 Implement Search, Activity, and Analytics pages
    - `/search` (keyword validation, results with Board and Column), `/boards/[boardId]/activity` (page-index navigation, empty page state), `/boards/[boardId]/analytics` (total, per-column counts, completion rate, activity by day)
    - _Requirements: 7.1, 7.2, 7.5, 8.12, 8.13, 8.15, 9.1, 9.2, 9.3, 9.5_

  - [ ] 17.8 Implement the Guest page
    - `/invite/[token]` calls only the two Guest endpoints through `apiClient`, renders read-only with no write controls, never redirects to `/login`, builds the Comment tree from `parentCommentId`, and shows one generic "link not available" message on `403`
    - _Requirements: 11.3, 11.4, 11.5, 11.6, 11.8_

- [ ] 18. Checkpoint - Ensure the frontend UI builds and passes checks
  - [ ] 18.1 Run all checks and commit
    - Backend (from `backend/`, venv active): `pytest`, `ruff check .`, `ruff format --check .`, `mypy .`
    - Frontend (from `frontend/`): `npm run lint`, `npm run build`, `npx playwright test` (skip while no E2E specs exist)
    - Fix every failure, ask the user if questions arise, then commit with the checkpoint number in the message

- [ ] 19. Playwright end-to-end tests
  - [ ] 19.1 Create E2E fixtures and helpers
    - `frontend/e2e/fixtures.ts`: helpers that create unique users, Teams, Boards, Cards, and Invitation_Links through the API (and the seed script for baseline data) so every test sets up its own data against the dedicated E2E test database configured in `playwright.config.ts` (task 1.6); accessible locators first, `data-testid` only for draggable Cards, no `waitForTimeout`
    - _Requirements: 14.5_

  - [ ] 19.2 Write auth E2E tests
    - `frontend/e2e/auth.spec.ts`: register, login, generic login error, logout, protected-route redirect to `/login`
    - _Requirements: 15.1, 15.2, 15.3, 15.8, 15.9_

  - [ ] 19.3 Write Team and join-link E2E tests
    - `frontend/e2e/teams.spec.ts`: create a Team, generate a join link, a second user previews and accepts it, invalid or revoked link message, regular members do not see link controls
    - _Requirements: 16.1, 16.4, 17.1, 17.2, 17.3, 17.4_

  - [ ] 19.4 Write Board, Column, and Card CRUD E2E tests
    - `frontend/e2e/boards.spec.ts`: create a Board with default Columns, add, rename, and delete Columns (non-empty delete rejected), create, edit, assign, and delete Cards, archive and restore, role-aware controls for a Member
    - _Requirements: 1.1, 1.2, 1.4, 1.5, 2.1, 2.2, 2.4, 3.1, 3.3, 3.4, 3.5_

  - [ ] 19.5 Write drag-and-drop E2E tests
    - `frontend/e2e/drag-and-drop.spec.ts`: move a Card across Columns and reorder within a Column, order persists after reload
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ] 19.6 Write Comment, Mention, and Notification E2E tests
    - `frontend/e2e/comments.spec.ts`: create a Comment, reply, edit, delete, mention another Member and see the Notification appear for them via polling and mark it read
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 6.1, 6.5_

  - [ ] 19.7 Write search E2E tests
    - `frontend/e2e/search.spec.ts`: case-insensitive title search with Board and Column shown, no-match empty state, blank keyword rejected
    - _Requirements: 7.1, 7.2, 7.4, 7.5_

  - [ ] 19.8 Write Guest access E2E tests
    - `frontend/e2e/guest.spec.ts`: anonymous visit of `/invite/[token]` shows the Board read-only with no write controls, a revoked or unknown token shows the generic message
    - _Requirements: 11.3, 11.4, 11.5, 11.6_

  - [ ] 19.9 Write responsive layout E2E tests
    - `frontend/e2e/responsive.spec.ts`: at >= 1024px the Board has no horizontal page scroll; below 1024px controls stay visible and non-overlapping
    - _Requirements: 14.3, 14.4_

- [ ] 20. Documentation, production seed, and smoke test
  - [ ] 20.1 Write the README
    - Root `README.md` (extend the "Deployment notes" created in task 4.9): setup (backend venv and `pip install -r requirements.txt`, frontend `npm install`, `.env` from `.env.example`, local PostgreSQL), run (backend and frontend commands), test (`pytest`, `ruff`, `mypy`, `npm run lint`, `npm run build`, `npx playwright test` with the dedicated E2E test database), deployment (Supabase, Render, Vercel, migrations and seeding run manually, open `/api/health` before demos), and the spec-driven workflow (requirements, design, tasks, CHANGELOG, steering)
    - Known limitations: free-tier backend sleep after idle (the first request and a proxied request may be slow or time out), Supabase Free project pause after a week of inactivity (restore it before demos), writes to archived Boards are not blocked in V1 (only Guest access is rejected), p95 < 300 ms (R14.1) and 99.5% availability (R14.2) are design targets rather than measured guarantees, and any dependency that failed to install in task 1.1
    - _Requirements: 14.1, 14.2_

  - [ ] 20.2 Seed the production database
    - From a developer machine, with the production `DATABASE_URL` set in the shell (never committed), run `python -m scripts.seed` from `backend/`; never run it at request time and never run E2E tests against production
    - Confirm the seeded demo data (users, Team, Board, Cards, Comment thread, Invitation_Link) is visible through the Vercel domain and record the demo credentials location (not the secrets) in the README
    - _Requirements: 1.2, 11.1_

  - [ ] 20.3 Run a manual production smoke test
    - On the Vercel domain (open `/api/health` first): log in, create a Board, drag a Card to another Column and reload to confirm the move persisted, open a Guest link in a private window and confirm it is read-only, and accept a Team join link as a second User
    - Check the headers: `curl -I https://<vercel-domain>/invite/<any-token>` and `curl -I https://<vercel-domain>/join/<any-token>` both return `Referrer-Policy: no-referrer`
    - Record the date, results, and any defects in the README "Deployment notes"; fix defects before the final checkpoint
    - _Requirements: 1.1, 4.1, 11.3, 15.2, 17.3_

- [ ] 21. Final checkpoint - Ensure all tests pass
  - [ ] 21.1 Run all checks and commit
    - Backend (from `backend/`, venv active): `pytest`, `ruff check .`, `ruff format --check .`, `mypy .`
    - Frontend (from `frontend/`): `npm run lint`, `npm run build`, `npx playwright test` (all E2E specs)
    - Fix every failure, ask the user if questions arise, then commit with the checkpoint number in the message

## Requirement-to-Task Mapping

Sub-task numbers that implement or test each acceptance criterion.

| Criterion | Sub-tasks |
| --- | --- |
| R1.1 | 7.1, 7.2, 17.1, 19.4, 20.3 |
| R1.2 | 7.1, 7.7, 13.1, 19.4 |
| R1.3 | 7.1, 7.3, 17.1 |
| R1.4 | 7.1, 7.7, 17.1, 19.4 |
| R1.5 | 7.1, 7.7, 17.1, 19.4 |
| R1.6 | 2.2, 2.4, 2.5, 7.1, 7.4, 17.1 |
| R1.7 | 5.2, 7.1, 7.7 |
| R1.8 | 7.1, 7.7, 11.12 |
| R1.9 | 7.1, 7.7 |
| R1.10 | 7.1, 7.3 |
| R1.11 | 7.1, 7.2 |
| R1.12 | 7.1, 7.2 |
| R1.13 | 7.1, 7.5, 17.1 |
| R1.14 | 7.1, 7.6 |
| R2.1 | 2.2, 9.1, 9.2, 9.4, 17.2, 19.4 |
| R2.2 | 9.1, 9.4, 17.2, 19.4 |
| R2.3 | 1.3, 2.4, 2.7, 9.1, 9.2, 17.2 |
| R2.4 | 9.1, 9.3, 17.2, 19.4 |
| R2.5 | 1.3, 9.1, 9.2 |
| R2.6 | 9.1, 9.4, 11.12 |
| R2.7 | 9.1, 9.4, 10.7 |
| R2.8 | 5.2, 9.1, 9.4 |
| R3.1 | 2.2, 10.1, 10.9, 17.2, 19.4 |
| R3.2 | 10.1, 10.5, 10.9 |
| R3.3 | 10.1, 10.3, 17.4, 19.4 |
| R3.4 | 10.1, 10.4, 17.4, 19.4 |
| R3.5 | 1.3, 10.1, 10.5, 17.4, 19.4 |
| R3.6 | 5.2, 10.1, 10.9 |
| R3.7 | 10.1, 11.12 |
| R3.8 | 10.1, 10.4 |
| R3.9 | 10.1, 10.9 |
| R3.10 | 10.1, 10.3 |
| R4.1 | 10.2, 10.5, 17.3, 19.5, 20.3 |
| R4.2 | 1.3, 2.4, 2.7, 10.2, 10.5, 17.3, 19.5 |
| R4.3 | 10.2, 10.6, 17.3, 19.5 |
| R4.4 | 10.2, 10.7 |
| R4.5 | 10.2, 10.7 |
| R4.6 | 5.2, 10.2, 10.9, 17.3 |
| R4.7 | 2.2, 2.4, 2.7, 10.2, 10.8 |
| R5.1 | 11.2, 17.5, 19.6 |
| R5.2 | 2.2, 2.5, 11.2, 11.8, 17.5, 19.6 |
| R5.3 | 11.2, 17.5, 19.6 |
| R5.4 | 11.2, 11.9, 17.5, 19.6 |
| R5.5 | 11.2, 11.10, 17.5 |
| R5.6 | 5.2, 11.2, 11.13 |
| R5.7 | 11.2, 11.12 |
| R5.8 | 11.2, 11.8 |
| R6.1 | 2.2, 2.5, 11.1, 11.2, 11.6, 17.5, 19.6 |
| R6.2 | 11.1, 11.7, 17.6 |
| R6.3 | 11.1, 11.7, 17.6 |
| R6.4 | 11.1, 11.7, 17.6 |
| R6.5 | 11.1, 11.13, 17.6, 19.6 |
| R6.6 | 11.1, 11.7, 17.6 |
| R6.7 | 1.3, 11.1, 11.7 |
| R6.8 | 11.1, 11.2, 11.6 |
| R6.9 | 11.1, 11.13 |
| R6.10 | 1.3, 1.4, 1.5, 11.1, 11.13 |
| R7.1 | 12.1, 12.3, 17.7, 19.7 |
| R7.2 | 12.1, 12.3, 17.7, 19.7 |
| R7.3 | 12.1, 12.3 |
| R7.4 | 12.1, 12.3, 19.7 |
| R7.5 | 12.1, 17.7, 19.7 |
| R7.6 | 12.1, 12.3 |
| R8.1 | 6.1, 10.1, 12.5 |
| R8.2 | 10.1, 12.5 |
| R8.3 | 10.2, 12.5 |
| R8.4 | 11.2, 12.5 |
| R8.5 | 10.1, 12.5 |
| R8.6 | 11.2, 12.5 |
| R8.7 | 11.2, 12.5 |
| R8.8 | 9.1, 9.4, 12.5 |
| R8.9 | 9.1, 9.4, 12.5 |
| R8.10 | 8.1, 12.5 |
| R8.11 | 8.1, 12.5 |
| R8.12 | 2.2, 2.5, 6.1, 6.2, 17.7 |
| R8.13 | 6.1, 12.5, 17.7 |
| R8.14 | 5.2, 6.1, 6.3 |
| R8.15 | 6.1, 6.2, 17.7 |
| R9.1 | 12.2, 12.4, 17.7 |
| R9.2 | 12.2, 12.4, 17.7 |
| R9.3 | 12.2, 12.4, 17.7 |
| R9.4 | 12.2, 12.4 |
| R9.5 | 12.2, 12.4, 17.7 |
| R9.6 | 12.2, 12.4 |
| R10.1 | 8.1, 8.3, 17.1 |
| R10.2 | 8.1, 8.5 |
| R10.3 | 8.1, 8.5, 17.1 |
| R10.4 | 8.1, 8.3 |
| R10.5 | 8.1, 8.3 |
| R10.6 | 8.1, 8.4 |
| R10.7 | 5.2, 8.1, 8.6 |
| R10.8 | 8.1, 8.3 |
| R10.9 | 8.1, 8.6, 17.1 |
| R11.1 | 2.2, 2.4, 8.2, 8.6, 11.4, 13.1, 17.1 |
| R11.2 | 8.2, 8.6, 11.4, 17.1 |
| R11.3 | 1.6, 11.3, 11.4, 11.5, 17.8, 19.8, 20.3 |
| R11.4 | 5.2, 11.3, 11.4, 11.5, 17.8, 19.8 |
| R11.5 | 11.3, 11.4, 17.8, 19.8 |
| R11.6 | 11.3, 11.4, 11.5, 17.8, 19.8 |
| R11.7 | 5.2, 8.2, 8.6 |
| R11.8 | 11.3, 11.4, 11.5, 17.8 |
| R11.9 | 8.2, 8.6, 17.1 |
| R12.1 | 5.1, 5.2 |
| R12.2 | 5.1, 5.2 |
| R12.3 | 5.1, 5.2 |
| R12.4 | 5.1, 5.2 |
| R12.5 | 5.1, 5.2 |
| R12.6 | 4.8, 5.1, 13.1, 13.2 |
| R13.1 | 10.1, 10.9, 11.2, 17.4 |
| R13.2 | 10.1, 11.2, 11.11, 15.1, 17.4, 17.5 |
| R13.3 | 10.1, 11.2, 11.11 |
| R13.4 | 2.2, 10.1, 10.9 |
| R13.5 | 1.2, 10.1, 11.2, 11.11, 17.4 |
| R13.6 | 10.1, 10.2, 10.8, 11.2 |
| R14.1 | design target, validated manually |
| R14.2 | 1.1, 1.2, 1.5, 4.9, 13.1, 20.1 |
| R14.3 | 1.6, 15.2, 17.2, 19.9 |
| R14.4 | 1.6, 15.2, 17.2, 19.9 |
| R14.5 | 11.11, 13.2, 19.1 |
| R15.1 | 2.1, 2.3, 4.1, 4.3, 15.3, 19.2 |
| R15.2 | 4.1, 4.2, 4.9, 15.1, 15.3, 19.2, 20.3 |
| R15.3 | 1.2, 4.1, 4.4, 15.3, 19.2 |
| R15.4 | 2.1, 4.1, 4.2, 4.7, 13.2 |
| R15.5 | 1.2, 4.1, 4.2, 4.7, 13.2 |
| R15.6 | 4.1, 4.2, 4.7 |
| R15.7 | 2.6, 4.1, 4.2, 4.7 |
| R15.8 | 2.1, 2.3, 4.1, 4.2, 4.6, 15.3, 19.2 |
| R15.9 | 4.1, 4.8, 15.3, 19.2 |
| R15.10 | 4.1, 4.8, 15.1 |
| R15.11 | 4.1, 4.2, 4.6, 15.1 |
| R15.12 | 4.1, 4.6, 15.1 |
| R15.13 | 4.1, 4.6 |
| R15.14 | 2.1, 4.1, 4.5, 15.3 |
| R15.15 | 2.1, 4.1, 4.2, 4.5 |
| R15.16 | 4.1, 4.5, 15.3 |
| R16.1 | 2.1, 2.3, 5.3, 5.4, 5.6, 16.1, 19.3 |
| R16.2 | 5.3, 5.4 |
| R16.3 | 5.3, 5.4, 16.1 |
| R16.4 | 5.3, 5.4, 16.1, 19.3 |
| R16.5 | 5.3, 5.4, 5.6 |
| R16.6 | 5.3 |
| R17.1 | 2.1, 2.3, 5.3, 5.5, 16.1, 19.3 |
| R17.2 | 5.3, 5.5, 16.1, 19.3 |
| R17.3 | 1.6, 5.3, 5.5, 5.6, 16.1, 19.3, 20.3 |
| R17.4 | 5.3, 5.5, 5.6, 16.1, 19.3 |
| R17.5 | 5.3, 5.5 |
| R17.6 | 5.3, 5.5 |
| R17.7 | 5.3, 5.5 |
| R17.8 | 5.3, 5.6, 16.1 |
| R17.9 | 5.3, 5.6, 16.1 |

## Property-to-Task Mapping

Each design property maps to exactly one backend property test sub-task.

| Property | Test sub-task | Test file |
| --- | --- | --- |
| P1 Column ordering is always contiguous from zero | 9.2 | `test_property_01_column_ordering.py` |
| P2 Card ordering is always contiguous from zero | 10.5 | `test_property_02_card_ordering.py` |
| P3 Card position round-trip persistence | 10.6 | `test_property_03_card_position_roundtrip.py` |
| P4 Out-of-range or cross-board moves leave position unchanged | 10.7 | `test_property_04_invalid_move_unchanged.py` |
| P5 Board partial update preserves omitted fields | 7.3 | `test_property_05_board_partial_update.py` |
| P6 Card edit is atomic across multiple fields | 10.3 | `test_property_06_card_edit_atomic.py` |
| P7 Input validation rejects invalid values | 11.12 | `test_property_07_input_validation.py` |
| P8 Assignment requires board membership | 10.4 | `test_property_08_assignee_membership.py` |
| P9 Non-empty column cannot be deleted | 9.3 | `test_property_09_nonempty_column_delete.py` |
| P10 Board permanent delete cascades completely | 7.4 | `test_property_10_board_cascade_delete.py` |
| P11 Comment deletion removes the entire reply subtree | 11.9 | `test_property_11_comment_subtree_delete.py` |
| P12 Reply threading validity | 11.8 | `test_property_12_reply_threading.py` |
| P13 Mentions create one unread notification per distinct board member | 11.6 | `test_property_13_mention_notifications.py` |
| P14 Notification cursor pagination | 11.7 | `test_property_14_notification_pagination.py` |
| P15 Notification cursor codec round-trip | 1.4 | `test_property_15_cursor_codec.py` |
| P16 Search result soundness, completeness, ordering, and cap | 12.3 | `test_property_16_search.py` |
| P17 Activity entries are recorded faithfully | 12.5 | `test_property_17_activity_recording.py` |
| P18 Activity pagination | 6.2 | `test_property_18_activity_pagination.py` |
| P19 Analytics counts and completion rate | 12.4 | `test_property_19_analytics.py` |
| P20 Optimistic concurrency prevents silent overwrites | 11.11 | `test_property_20_optimistic_concurrency.py` |
| P21 RBAC decisions match the capability matrix | 5.2 | `test_property_21_rbac_matrix.py` |
| P22 Authentication gate precedes authorization | 4.8 | `test_property_22_auth_gate.py` |
| P23 Board retains at least one Admin | 8.4 | `test_property_23_last_admin.py` |
| P24 Role changes apply on the next request | 8.5 | `test_property_24_role_change_next_request.py` |
| P25 Invitation link generation, isolation, and Guest access control | 11.4 | `test_property_25_invitation_guest_access.py` |
| P26 Passwords are stored as a verifiable argon2 hash | 4.3 | `test_property_26_password_hash.py` |
| P27 Login failures do not disclose which field was wrong | 4.4 | `test_property_27_generic_login_error.py` |
| P28 Registration validation | 4.5 | `test_property_28_registration_validation.py` |
| P29 Refresh-token exchange and revocation | 4.6 | `test_property_29_refresh_token.py` |
| P30 Account lockout after three consecutive failed logins | 4.7 | `test_property_30_account_lockout.py` |
| P31 Team creation, listing, membership, and access control | 5.4 | `test_property_31_teams.py` |
| P32 Board creation grants the creator Admin immediately | 7.2 | `test_property_32_board_creation.py` |
| P33 Board invitations require an eligible Team_Member | 8.3 | `test_property_33_board_invitations.py` |
| P34 Team_Join_Link lifecycle and access control | 5.5 | `test_property_34_team_join_link.py` |
| P35 Card move changes only the moved Card's updated_at | 10.8 | `test_property_35_move_updated_at_version.py` |
| P36 Activity is readable only by Members and Admins | 6.3 | `test_property_36_activity_access.py` |
| P37 Board list reflects the caller's roles and the archived filter | 7.5 | `test_property_37_board_list.py` |
| P38 Visibility does not change who can access a Board | 7.6 | `test_property_38_visibility_no_effect.py` |
| P39 Only the author can edit or delete a Comment | 11.10 | `test_property_39_comment_ownership.py` |

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3"] },
    { "id": 3, "tasks": ["1.4"] },
    { "id": 4, "tasks": ["1.5"] },
    { "id": 5, "tasks": ["1.6"] },
    { "id": 6, "tasks": ["2.1"] },
    { "id": 7, "tasks": ["2.2"] },
    { "id": 8, "tasks": ["2.3"] },
    { "id": 9, "tasks": ["2.4"] },
    { "id": 10, "tasks": ["2.5"] },
    { "id": 11, "tasks": ["2.6"] },
    { "id": 12, "tasks": ["2.7"] },
    { "id": 13, "tasks": ["3.1"] },
    { "id": 14, "tasks": ["4.1"] },
    { "id": 15, "tasks": ["4.2"] },
    { "id": 16, "tasks": ["4.3"] },
    { "id": 17, "tasks": ["4.4"] },
    { "id": 18, "tasks": ["4.5"] },
    { "id": 19, "tasks": ["4.6"] },
    { "id": 20, "tasks": ["4.7"] },
    { "id": 21, "tasks": ["4.8"] },
    { "id": 22, "tasks": ["4.9"] },
    { "id": 23, "tasks": ["5.1"] },
    { "id": 24, "tasks": ["5.2"] },
    { "id": 25, "tasks": ["5.3"] },
    { "id": 26, "tasks": ["5.4"] },
    { "id": 27, "tasks": ["5.5"] },
    { "id": 28, "tasks": ["5.6"] },
    { "id": 29, "tasks": ["6.1"] },
    { "id": 30, "tasks": ["6.2"] },
    { "id": 31, "tasks": ["6.3"] },
    { "id": 32, "tasks": ["7.1"] },
    { "id": 33, "tasks": ["7.2"] },
    { "id": 34, "tasks": ["7.3"] },
    { "id": 35, "tasks": ["7.4"] },
    { "id": 36, "tasks": ["7.5"] },
    { "id": 37, "tasks": ["7.6"] },
    { "id": 38, "tasks": ["7.7"] },
    { "id": 39, "tasks": ["8.1"] },
    { "id": 40, "tasks": ["8.2"] },
    { "id": 41, "tasks": ["8.3"] },
    { "id": 42, "tasks": ["8.4"] },
    { "id": 43, "tasks": ["8.5"] },
    { "id": 44, "tasks": ["8.6"] },
    { "id": 45, "tasks": ["9.1"] },
    { "id": 46, "tasks": ["9.2"] },
    { "id": 47, "tasks": ["9.3"] },
    { "id": 48, "tasks": ["9.4"] },
    { "id": 49, "tasks": ["10.1"] },
    { "id": 50, "tasks": ["10.2"] },
    { "id": 51, "tasks": ["10.3"] },
    { "id": 52, "tasks": ["10.4"] },
    { "id": 53, "tasks": ["10.5"] },
    { "id": 54, "tasks": ["10.6"] },
    { "id": 55, "tasks": ["10.7"] },
    { "id": 56, "tasks": ["10.8"] },
    { "id": 57, "tasks": ["10.9"] },
    { "id": 58, "tasks": ["11.1"] },
    { "id": 59, "tasks": ["11.2"] },
    { "id": 60, "tasks": ["11.3"] },
    { "id": 61, "tasks": ["11.4"] },
    { "id": 62, "tasks": ["11.5"] },
    { "id": 63, "tasks": ["11.6"] },
    { "id": 64, "tasks": ["11.7"] },
    { "id": 65, "tasks": ["11.8"] },
    { "id": 66, "tasks": ["11.9"] },
    { "id": 67, "tasks": ["11.10"] },
    { "id": 68, "tasks": ["11.11"] },
    { "id": 69, "tasks": ["11.12"] },
    { "id": 70, "tasks": ["11.13"] },
    { "id": 71, "tasks": ["12.1"] },
    { "id": 72, "tasks": ["12.2"] },
    { "id": 73, "tasks": ["12.3"] },
    { "id": 74, "tasks": ["12.4"] },
    { "id": 75, "tasks": ["12.5"] },
    { "id": 76, "tasks": ["13.1"] },
    { "id": 77, "tasks": ["13.2"] },
    { "id": 78, "tasks": ["14.1"] },
    { "id": 79, "tasks": ["15.1"] },
    { "id": 80, "tasks": ["15.2"] },
    { "id": 81, "tasks": ["15.3"] },
    { "id": 82, "tasks": ["16.1"] },
    { "id": 83, "tasks": ["17.1"] },
    { "id": 84, "tasks": ["17.2"] },
    { "id": 85, "tasks": ["17.3"] },
    { "id": 86, "tasks": ["17.4"] },
    { "id": 87, "tasks": ["17.5"] },
    { "id": 88, "tasks": ["17.6"] },
    { "id": 89, "tasks": ["17.7"] },
    { "id": 90, "tasks": ["17.8"] },
    { "id": 91, "tasks": ["18.1"] },
    { "id": 92, "tasks": ["19.1"] },
    { "id": 93, "tasks": ["19.2"] },
    { "id": 94, "tasks": ["19.3"] },
    { "id": 95, "tasks": ["19.4"] },
    { "id": 96, "tasks": ["19.5"] },
    { "id": 97, "tasks": ["19.6"] },
    { "id": 98, "tasks": ["19.7"] },
    { "id": 99, "tasks": ["19.8"] },
    { "id": 100, "tasks": ["19.9"] },
    { "id": 101, "tasks": ["20.1"] },
    { "id": 102, "tasks": ["20.2"] },
    { "id": 103, "tasks": ["20.3"] },
    { "id": 104, "tasks": ["21.1"] }
  ]
}
```
