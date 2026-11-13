---
inclusion: fileMatch
fileMatchPattern: "backend/**/*.py"
---

# Backend Guidelines (Flask)

Layering, transactions, and the error model are in `tech.md` and
`card-conventions.md` (rules 1-2); tables and models are in `database.md`;
folder layout is in `structure.md`. This file covers how Flask code is written.

## 1. Blueprint per module
**Rule:** Each module under `backend/flask_app/<module>/` defines one Blueprint
in `routes.py`, input schemas in `schema.py`, and logic in `service.py`, and
exports the Blueprint from `__init__.py`. Route paths are written in full
starting with `/api` (no `url_prefix`). Blueprints are registered in `app.py`.
Handlers follow `card-conventions.md` rule 1 (max 5 lines).
**Rationale:** Identical layout per module, so the agent always knows where code goes.
**Example:** `cards/{routes,schema,service}.py`; `cards/routes.py` defines `cards_bp`.

## 2. Authentication and role decorators
**Rule:** `@token_required` (in `auth/`) reads the access token from its cookie,
loads the User, and raises `AuthenticationError` before the handler runs.
`@require_role('member' | 'admin')` (in `access/rbac.py`) applies the same
check first, then resolves the Board from the route parameters and reads the
User's role from stored membership in the database, never from the token.
Routes needing only identity (teams, notifications, search, `GET /api/auth/me`)
use `@token_required`. Public routes are only: `GET /api/health`,
`POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/refresh` and
`POST /api/auth/logout` (authenticated by the refresh cookie), and the Guest
routes in rule 3. Any other route must carry a decorator; ask before adding a
public route. State-changing routes never use GET.
**Rationale:** Authentication always precedes authorization (R12.6), and roles
stay current (R12.1).
**Example:** `@require_role('admin')` on `POST /api/columns/<uuid:column_id>/reorder`.

## 3. Guest routes
**Rule:** Guest endpoints live under `/api/guest/<token>/...`, are GET only,
and need no authentication. There are two: `GET /api/guest/<token>/board`
(Board name, description, `currentUserRole: "guest"`, with its Columns and
Cards) and `GET /api/guest/<token>/cards/<uuid:card_id>/comments` (a flat list
of Comments with `parentCommentId`, oldest first). One function in `access/`
resolves the token to its Board and raises `AuthorizationError` for an unknown,
inactive, or revoked token, and for a token whose Board is archived. A Card that
does not belong to the token's Board raises `NotFoundError`. Guest responses
never include emails, `version`, or Activity data; Users appear only as
`{ id, displayName }`. Any other HTTP method on `/api/guest/` returns 403
`AuthorizationError`, not 405.
**Rationale:** Guests are anonymous and read-only (R11.3, R11.4), and must learn
nothing about other Boards.
**Example:** `GET /api/guest/<token>/board` returns the Board with its Columns and Cards.

## 4. Input validation (Marshmallow)
**Rule:** Every request body and query string is validated by a Marshmallow
schema in the module's `schema.py` before the service runs. The route calls
`load_schema(CreateCardSchema(), read_json())`, or `read_query()` for query
strings. Both live in `common/`. Conventions:
- All schemas inherit `BaseSchema` (`common/validation.py`) with
  `unknown = RAISE`, so unexpected fields are rejected.
- `read_json()` and `read_query()` already convert camelCase keys to
  snake_case, so schemas use snake_case field names and never `data_key`.
- Names, titles, and display names use `TrimmedStr` (trims first, then runs the
  length validator, so lengths count after trimming). Comment bodies use
  `NonBlankStr` (requires a non-whitespace character, stored unchanged).
  Passwords are never trimmed.
- Create schemas mark required fields. Update (PATCH) schemas make every
  editable field optional and set no `load_default`, so an omitted field is
  absent from the result and stays unchanged (R1.3). The whole body is
  validated before any write, so a multi-field request is atomic (R1.10, R3.10).
- `version` is never `required` in a schema: a missing `version` raises
  `ConflictError` in the service (R13.5); a present non-integer `version` is a
  validation error.
- Rules that need the database (the Assignee is a Board Member, the target
  index is in range, the parent Comment is on the same Card) run in the service
  before the first write, not in the schema.
- `load_schema` converts Marshmallow's error into our `ValidationError`,
  reporting the first failing field. A body that is not a JSON object gives an
  error with no field. Keep schemas flat in V1 (no nested schemas).
- Schemas are for input only. Response dicts are built by plain functions in
  `service.py`, and `json_response()` formats UUIDs and timestamps. Never use
  schema `dump` for responses.
**Rationale:** Bad input never reaches the database, and the shape rules are
testable without HTTP.
**Example:**
```python
class CreateCardSchema(BaseSchema):
    title = TrimmedStr(required=True, validate=validate.Length(min=1, max=255))

class UpdateCardSchema(BaseSchema):
    title = TrimmedStr(validate=validate.Length(min=1, max=255))
    description = fields.Str(validate=validate.Length(max=5000))
    version = fields.Int(strict=True)  # missing -> ConflictError in the service
```

## 5. Response format
**Rule:** Success returns the resource or result directly through
`json_response()`, with no `data` wrapper. Status codes: 201 for create, 200 for
other successes, 204 with no body for deletes. Paginated endpoints return
`{ "items": [...] }` plus the cursor field defined in `design.md`. Errors are
always `{ "error": { "code", "message", "field?" } }`: never a bare string, a
field map, HTML, or a traceback.
**Rationale:** The frontend parses every response the same way.
**Example:** `POST /api/columns/<uuid:column_id>/cards` returns `201` with the
created Card.

## 6. Error mapping
**Rule:** One global handler in `app.py` maps `ValidationError` to 400,
`AuthenticationError` to 401, `AuthorizationError` to 403, `NotFoundError` to
404, and `ConflictError` to 409. It also maps Werkzeug `HTTPException`s (unknown
URL, bad method) to the same envelope, and maps any unexpected exception to 500
`{ "error": { "code": "internal_error", "message": "Internal server error" } }`
after logging the traceback server-side. Every error handler rolls back the
session. Error `code` values are snake_case constants defined in `exceptions.py`.
Messages never contain SQL, secrets, or whether an account exists or is locked
(R15.3, R15.5).
**Rationale:** One place owns the error-to-HTTP mapping.
**Example:** `raise NotFoundError('Card not found')` returns 404 with code `not_found`.

## 7. Unit of work
**Rule:** Each service function that a route calls is exactly one transaction:
it performs all writes, including reindexing, Activity_Entry, and Notification
creation, and commits once at the end. Helpers (`reindex`, `record_activity`,
mention-notification creation) only add to the session and never commit. Before
reindexing a Column, lock the affected Column row with `with_for_update()` so
concurrent moves do not interleave.
**Rationale:** An activity or notification exists if and only if its triggering
mutation succeeded (R8, R6.1).
**Example:** `move_card_service` reindexes, records "card moved", and calls
`db.session.commit()` once.

## 8. Auth cookies and tokens
**Rule:** Only `auth/` sets or clears cookies, through `set_auth_cookies()` and
`clear_auth_cookies()`, using names, lifetimes, and the `Secure` flag from
`config.py`. Flags follow `tech.md` (Security). Tokens never appear in response
bodies or logs. Passwords are hashed with argon2 in `auth/` only. Login
lockout (R15.4-R15.7) reads time through `utc_now()` from `common/time.py`, so
tests can control the clock. Refresh and invitation tokens are generated with
`secrets.token_urlsafe`.
**Rationale:** Token handling lives in one reviewed place.
**Example:** A successful login calls `set_auth_cookies(response, access, refresh)`.

## 9. Configuration
**Rule:** All settings come from environment variables through `config.py`
(`DATABASE_URL`, `JWT_SECRET_KEY`, `COOKIE_SECURE`, ...). No `os.environ`
elsewhere. A missing required setting fails fast at startup. Debug is off in
production.
**Rationale:** One place to see and validate configuration.
**Example:** `current_app.config['COOKIE_SECURE']`, not `os.environ['COOKIE_SECURE']`.

## 10. Queries and pagination
**Rule:** No N+1 queries (eager-load per `database.md` rule 5). Page sizes and
caps are server-side constants in one module and never client-controlled:
Notifications 50, Activity 100, Search 100. Search escapes `%`, `_`, and `\` in
the keyword before a case-insensitive `ILIKE`, so the keyword is a literal
substring (R7.1). Ordering is `created_at DESC, id DESC` unless the spec says
otherwise.
**Rationale:** Meets R14.1 and keeps ordering deterministic.
**Example:** `NOTIFICATIONS_PAGE_SIZE = 50` in `common/pagination.py`.

## 11. Logging
**Rule:** Use `app.logger`. Log the HTTP method, the route template (for example
`/api/guest/<token>/board`, from `request.url_rule.rule`; use `unmatched` when
there is no matching rule), the status, and the user id. Never log the raw
request path or query string, passwords, tokens (including Invitation_Link and
Team_Join_Link tokens), cookies, request bodies, or Comment text. Do not enable
gunicorn's access log with the default format, because it prints the raw path.
**Rationale:** Guest and join tokens are credentials that appear in URLs, and
logs must be safe to share and to read in a deployment dashboard.
**Example:** `app.logger.info("%s %s -> %s user=%s", request.method, rule, status, user_id)`

## 12. Mentions
**Rule:** A Mention is the token `@[<user-uuid>]` inside a Comment body. The
mention parser lives in `comments/service.py` as a pure function that extracts
distinct, valid UUIDs from the body. After the Comment is saved, create exactly
one Notification per distinct mentioned User who is a current Member of the
Board and ignore all other ids, in the same transaction as the Comment (R6.1,
R6.8). Never reject a Comment because a mention is invalid.
**Rationale:** Mentions are parsed in one place and cannot fail a Comment.
**Example:** `"Please review @[3f2b...] and @[3f2b...]"` creates one Notification.