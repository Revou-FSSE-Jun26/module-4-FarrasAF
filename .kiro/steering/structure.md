---
inclusion: always
---

# Project Structure

Monorepo: one repository, separate `backend/` and `frontend/` folders.
Specs and steering live in `.kiro/`. Architecture details are in
`.kiro/specs/task-management-app/design.md`.

## Top-Level Layout
```
task-management-app/
├── .kiro/
│   ├── specs/task-management-app/   # requirements.md, design.md, tasks.md
│   └── steering/                    # product, tech, structure, frontend, card-conventions
├── backend/                         # Flask API
├── frontend/                        # Next.js app (+ Playwright E2E)
├── README.md
└── .gitignore
```

## Backend (`backend/`)
```
backend/
├── flask_app/
│   ├── __init__.py
│   ├── app.py                # app factory (create_app), blueprint registration, error handlers
│   ├── extensions.py         # SQLAlchemy db, migrate
│   ├── config.py             # settings from env (DATABASE_URL, JWT_SECRET_KEY, COOKIE_SECURE, ...)
│   ├── models/               # one file per entity; __init__.py imports all models so Alembic sees them
│   ├── auth/                 # Authentication_Service (login, refresh, logout, auth cookies)
│   ├── access/               # Access_Control_Service (membership, invitations); rbac.py holds the
│   │                         # require_role decorator and the pure role-decision function
│   ├── boards/               # Board_Service
│   ├── columns/              # Column_Service
│   ├── cards/                # Card_Service
│   ├── comments/             # Comment_Service
│   ├── notifications/        # Notification_Service
│   ├── search/               # Search_Service
│   ├── activity/             # Activity_Service
│   ├── analytics/            # Analytics_Service
│   └── common/               # exceptions.py, validation.py, ordering.py (reindex), cursor.py,
│                             # serialization.py (snake_case <-> camelCase), health.py (GET /api/health)
├── migrations/               # Alembic (never hand-edit applied migrations)
├── scripts/
│   ├── __init__.py
│   └── seed.py               # demo and E2E seed data (run: python -m scripts.seed)
├── tests/
│   ├── conftest.py           # shared fixtures (test DB session, users, boards)
│   ├── unit/
│   ├── properties/
│   └── integration/
├── requirements.txt
├── .env.example              # DATABASE_URL, JWT_SECRET_KEY, COOKIE_SECURE, ...
└── pyproject.toml            # ruff and mypy config
```

### Backend module convention
Each service package (`cards/`, `boards/`, ...) contains:
- `routes.py`: Flask blueprint; thin handlers only
- `service.py`: business logic (`*_service` functions)
- `__init__.py`: exports the blueprint

Cross-module calls go through service functions, never through another
module's routes. Models live only in `models/`.

Exceptions to the convention: `common/health.py` (public `GET /api/health`, no auth, never touches the database) and `access/rbac.py`.

## Frontend (`frontend/`)
```
frontend/
├── src/                          # ALL application code lives here
│   ├── app/                      # Next.js App Router (page.tsx per route)
│   │   ├── login/
│   │   ├── register/
│   │   ├── boards/
│   │   │   └── [boardId]/        # board view, activity/, analytics/, settings/
│   │   ├── invite/[token]/       # guest view
│   │   └── search/
│   ├── components/
│   │   ├── shared/               # Base* primitives (BaseButton, BaseModal, ...)
│   │   └── <feature>/            # board/, card/, comment/, notification/, ...
│   ├── hooks/                    # useXxx.ts custom hooks
│   ├── lib/                      # apiClient.ts (same origin /api calls, cookie-based auth), pure utilities
│   └── types/
│       └── api.ts                # API request/response types mirroring design.md
├── e2e/                          # Playwright tests (*.spec.ts) and fixtures
├── public/                       # static assets
├── playwright.config.ts
├── next.config.ts                # rewrites /api/:path* to the backend (API_URL)
├── tsconfig.json                 # alias "@/*" -> "./src/*"
├── package.json
└── .env.example                  # API_URL (server-side, used by the rewrite)
```

### Frontend placement rules
- Application code goes under `frontend/src/` only. Never create `app/`,
  `components/`, `hooks/`, `lib/`, or `types/` at the `frontend/` root
  (Next.js would ignore `src/app/` if a root `app/` exists).
- `e2e/`, `public/`, and config files stay outside `src/`.
- Import with the `@/` alias (maps to `src/`), e.g. `import { Card } from '@/types/api'`.

## Where New Code Goes
- New endpoint: `routes.py` + `service.py` in the matching backend module
- New table: `backend/flask_app/models/` + a new Alembic migration
- New shared validation or helper: `backend/flask_app/common/`
- New page: folder with `page.tsx` under `frontend/src/app/`
- New feature component: `frontend/src/components/<feature>/`
- New shared primitive: `frontend/src/components/shared/Base*.tsx`
- New hook: `frontend/src/hooks/useXxx.ts`
- New API type: `frontend/src/types/api.ts`; new HTTP call: `frontend/src/lib/apiClient.ts`
- New E2E test: `frontend/e2e/<flow>.spec.ts`
- New JSON field name conversion: only in `backend/flask_app/common/serialization.py`
- New RBAC rule: `backend/flask_app/access/rbac.py`
- New public (no-auth) endpoint: only `common/health.py` and the auth routes; ask before adding others

## Naming
- Backend follows `card-conventions.md` (snake_case; tables plural_snake_case)
- Frontend follows `frontend.md`
- Test files: backend `test_<module>.py`; property tests
  `test_property_<n>_<short_name>.py`; E2E `<flow>.spec.ts`
- Route params use `[boardId]`, matching the API in `design.md`

## Rules
- Run backend commands from `backend/`, frontend commands from `frontend/`
- Frontend never imports from `backend/`; the contract is the REST API
- No secrets in the repo; each app has its own `.env.example`
- `README.md` at the root documents setup, run, test, and the spec-driven workflow
- The browser only calls same-origin `/api/*` paths; Next.js rewrites them to
  the backend (see `tech.md`). Never hard-code the backend URL in `src/`.
- Do not add Docker files. Platform config (e.g. `render.yaml`) is optional
  and lives at the repo root if used.