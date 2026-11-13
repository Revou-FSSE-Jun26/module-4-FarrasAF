# Changelog

All notable changes to the task-management-app spec are documented here. Versions are ordered newest-first. The version is bumped each time a spec document (requirements.md, design.md, or tasks.md) is changed.

## v12 - 2026-11-13 - Design aligned to identity-only cookie auth, Teams, Guest endpoints, and API conventions

### Changes
Design-only revision (design.md). requirements.md and the steering files were not modified. Existing property numbers and R{n}.{m} references were preserved; only the Correctness Properties listed below were edited.

- **Technology Stack / Topology / Design Goals:** pinned Python 3.14, argon2 (`argon2-cffi`), Marshmallow input validation, `@dnd-kit/core` + `@dnd-kit/sortable`, `frontend/src/`, `backend/flask_app/` (routes.py + schema.py + service.py per module, plus a `teams/` module), Supabase/Render/Vercel deployment, same-origin `/api/*` with no CORS, and the public `GET /api/health` note.
- **Auth model (identity-only cookies):** Access_Token (15 min) and Refresh_Token (7 days) now carry identity only (no role or Team claims, R15.13) and travel in `HttpOnly` cookies (`SameSite=Lax`, `Secure` via `COOKIE_SECURE`, refresh cookie scoped to `/api/auth/refresh` and `/api/auth/logout`). Login sets both cookies and returns identity; registration creates an account only (no auto-login); logout is authenticated by the refresh cookie, clears both cookies, and revokes the refresh token.
- **Roles from stored membership:** Request Flow, RBAC Enforcement, and the role paragraph now resolve roles from stored `BoardMembership`/`TeamMembership` on every request; a role change or removal applies on the next request with no token refresh. Board responses carry `currentUserRole`; Team responses carry `currentUserTeamRole`; `GET /api/auth/me` returns identity only.
- **Service responsibilities / layering:** added Team_Service (`teams/`) and the Guest-route split in `access/`; documented `@token_required`, `@require_role('member'|'admin')`, Marshmallow + `load_schema`, and `read_json`/`read_query`/`json_response` as cross-cutting interfaces; updated the backend tree and `common/` files.
- **Data Models:** added TeamMembership `team_role`, Team creator = `team_admin`, and a new TeamJoinLink entity (7-day expiry computed at read time); `BaseModel` four-column shape; Card `updated_at` no-`onupdate` exception; deferrable order-index uniqueness; hard deletes; RefreshToken hashed; enum string values fixed to stored form; Board-delete cascade list expanded.
- **API Design:** added common conventions (camelCase keys only, unwrapped responses, `DELETE` 204, no `If-Match`, UUID/ISO-8601, public-endpoint list, server-enforced pagination, role fields). Added Team_Service endpoints (R16, R17), Guest endpoints under `/api/guest/{token}/...` (GET only), `GET /api/boards/{boardId}/members`, `GET /api/boards/{boardId}/invitations`, and `POST /api/boards/{boardId}/members` with the Team-member check. Every endpoint row is tagged with the requirement numbers it satisfies.
- **Error Handling:** `ConflictError` (409) restricted to Card/Comment version conflicts only; duplicate email, already-member, last-admin, and restore-of-non-archived moved to `ValidationError` (400); added Team/join-link validation rows, Guest-route `403`-on-non-GET, Werkzeug `HTTPException` mapping, and the `500 internal_error` fallback. Added search `%`/`_`/`\` escaping and the cookie/logging security notes.
- **Correctness Properties:** edited only Property 21 (role read from stored membership; anonymous Guest), Property 22 (token in cookie; public/Guest routes exempt), Property 24 (renamed/rewritten: role changes apply on the next request from stored membership; now Validates 10.2, 10.3), and Property 29 (refresh yields an identity-only access token, no role claims). Total remains 30.
- **Testing Strategy:** removed `fast-check`; Playwright E2E is the sole frontend test type (added Team/join and Guest flows); updated auth example-test wording to cookies/identity-only and added Team and Guest edge cases.

### Reason
Bring design.md into agreement with the finalized DECISIONS and requirements.md (notably R15.13 identity-only tokens, R16/R17 Teams and Team_Join_Links, anonymous Guest endpoints, and the API/convention rules in the steering files). The previous design still described a JWT-embedded-role-claims model that contradicted R10.3/R12.1 and R15.13.

### Impact
- Affected requirements: alignment across R1, R3, R4, R5, R6, R7, R8, R10, R11, R12, R13, R15, R16, R17 (no requirement text changed).
- Affected design components: Technology Stack, Design Goals, Topology, Request Flow, Service Responsibilities, Backend Layering, Cross-Cutting Interfaces, Frontend Structure, Data Models, Version/Concurrency, API Design (all service tables), Authentication & Authorization, Key Behaviors (cascade/archive), Correctness Properties 21/22/24/29, Error Handling, Testing Strategy.
- Affected implementation tasks: none yet (tasks.md not created).

## v11 - Account lockout after failed logins
- Req 15 (requirements.md): added account lockout — three consecutive failed login attempts lock an account for 15 minutes (Req 15.4); while locked, all login attempts are rejected with the generic authentication error and no tokens are issued even with correct credentials, without disclosing the locked state (Req 15.5); a successful login resets the consecutive-failure count (Req 15.6); the count resets and logins resume after the 15-minute window elapses (Req 15.7).
- Req 15 renumbering: inserting the four lockout criteria shifted later criteria — logout is now 15.8, unauthenticated-access 15.9, expired/invalid access token 15.10, refresh success 15.11, refresh failure 15.12, role-claim embedding 15.13, registration validation 15.14/15.16, duplicate-email 15.15.
- Design (design.md): added account-lockout behavior to the Session/Token Model; added User fields failed_login_attempts and locked_until for lockout tracking; noted lockout enforcement on the login endpoint; added locked-account handling to the AuthenticationError taxonomy; added a brute-force mitigation security note; added Property 30 (account lockout) bringing the total to 30 correctness properties; updated all shifted R15.x references to the new numbering; added lockout/unlock integration-test coverage with a controllable-clock note.

## v10 - Design aligned to JWT authentication model
- Technology Stack ("Auth"): replaced server-issued session token with stateless short-lived JWT access tokens + longer-lived revocable refresh tokens.
- High-Level Topology diagram: Browser edges now labeled "HTTPS REST + JWT access token".
- Request Flow + sequence diagram: validate JWT signature/expiry; role claims read from the JWT access token so role changes take effect only after access-token refresh/re-issue (R10.3).
- Service Responsibilities: Authentication_Service row now covers logout (refresh-token revocation), JWT access-token issuance, and token refresh (R15, R12.6).
- Authentication & Authorization > Session/Token Model: rewritten for the JWT model (login issues access JWT + refresh token R15.2; per-request JWT validation R15.5/15.6/12.6; authorization reads JWT role claims R12/R10.3; logout revokes refresh token R15.4; refresh issues new access token R15.7/15.9 and rejects revoked/expired/invalid R15.8; registration refs shifted to R15.10/15.11/15.12).
- RBAC decorator description: resolves role from the JWT access token's role claims.
- Data Models: added RefreshToken entity (hashed token, revocable) and ER edge USER ||--o{ REFRESH_TOKEN; noted access tokens are stateless/not stored; User duplicate-email note shifted to R15.11.
- API Design: intro now requires a valid JWT access token; Authentication_Service table updated (register R15.1/15.10/15.11/15.12, login returns access+refresh R15.2/15.3, logout revokes refresh R15.4, new POST /api/auth/refresh R15.7/15.8/15.9, GET /api/auth/me reads access-token claims R15.6).
- Frontend Structure: API client attaches the JWT access token and refreshes it via the refresh endpoint when expired.
- Error Handling + Security Considerations: AuthenticationError covers invalid JWT access tokens and refresh rejection (R15.8); refresh tokens stored hashed and revocable, access tokens stateless/short-lived; registration refs shifted to R15.10/15.11/15.12.
- Correctness Properties: Property 22 reworded to "JWT access token"; Property 24 reworded to refreshed/re-issued access token; Property 28 Validates updated to R15.10/15.12; added Property 29 (refresh-token exchange and revocation, R15.7/15.8/15.9). Total property count now 29.
- Testing Strategy: updated the "29 correctness properties" count and the example-based auth coverage (login access+refresh R15.2, logout revocation R15.4, token refresh R15.7).

## v9 - JWT-based authentication model
- Req 15 (User Authentication): specified a short-lived access JWT plus longer-lived refresh token model.
- Req 15.2: login now issues an Access_Token (JWT with identity and role claims) and a Refresh_Token.
- Req 15.4: logout now revokes the Refresh_Token instead of invalidating a server session.
- Req 15.6: expired/invalid token rejection now refers to the Access_Token (JWT).
- Req 15.7 (new): token refresh issues a new Access_Token from a valid Refresh_Token.
- Req 15.8 (new): revoked/expired/invalid Refresh_Token refresh is rejected with no Access_Token issued.
- Req 15.9 (new): Access_Tokens embed role claims current at issuance (consistent with Req 10.3).
- Renumbered registration criteria to 15.10-15.12.
- Glossary: added Access_Token and Refresh_Token; updated Session and Authentication_Service to reference JWT issuance and refresh.
- Introduction: noted that successful authentication issues a JWT-based access token.

## v8 - Technical design document
- Created design.md from the finalized requirements (requirements-first workflow).
- Added architecture (Next.js + Flask + PostgreSQL), two-gate request flow (authentication then RBAC), and a service breakdown mapped to the requirements glossary.
- Added the SQLAlchemy data model, REST API design, session/token auth model, key invariants, 28 property-based correctness properties, error taxonomy, and testing strategy.

## v7 - Requirements analysis round 2
- Req 4.1: card move now applies to any authorized non-Guest role (Member or Admin).
- Req 1: added atomic multi-field board update (any invalid field rejects the whole request).
- Req 3: added atomic multi-field card edit.
- Req 9.3: completion rate now sums cards across all columns named "Done".
- Req 10.3: role changes take effect only after the member's session/token is refreshed.

## v6 - Expanded activity log events
- Req 8: added recorded events for card deleted, comment deleted, comment edited, column created, column deleted, member joined, and member removed.

## v5 - Unified notification pagination + unread filter
- Req 6: the general notification list now uses cursor pagination (max 50 per page).
- Added an unread-only filter.
- Broadened malformed-cursor validation to cover all notification retrieval paths.

## v4 - Notification cursor pagination
- Req 6 AC4: replaced timestamp-based polling with cursor pagination based on a combined (timestamp, ID) cursor; the cursor is optional, and omitting it returns the newest page.
- Added the Notification_Cursor glossary term.

## v3 - User authentication and manual edits
- Added Requirement 15 (User Authentication): registration, login, logout, session handling, and registration validation.
- Added Authentication_Service and Session glossary terms; updated the User definition and Introduction; cross-linked RBAC (Req 12).
- Preserved the user's manual Requirement 2 edits (empty-column-before-delete model).

## v2 - Requirements analysis round 1
- Req 1.3: board updates support partial field updates.
- Req 8: activity log uses numbered-page pagination, with an empty page for out-of-range indices.
- Req 7.6: search adds a deterministic Card-ID tie-break at the 100-result cap.

## v1 - Initial generation
- Generated requirements.md with 14 requirements covering boards, columns, cards, drag-and-drop, comments, mention notifications, search, activity log, analytics, members and roles, invitation links, RBAC, concurrency, and non-functional targets.
- Each requirement was detailed into precise, testable EARS acceptance criteria.
