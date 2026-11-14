# Changelog

All notable changes to the task-management-app spec are documented here. Versions are ordered newest-first. The version is bumped each time a spec document (requirements.md, design.md, or tasks.md) is changed.

## v17 - 2026-11-13 - tasks.md created

### Changes
Implementation plan created (tasks.md). requirements.md, design.md, and the steering files were not modified, and no requirement, property, or endpoint was renumbered.

- Added tasks.md: 19 top-level tasks covering backend foundation, models and migrations, authentication, RBAC and Teams, Activity, Boards, access control and Guest routes, Columns, Cards, Notifications and Comments, Search and Analytics, backend wiring and seed data, frontend foundation and UI, Playwright E2E, and checkpoints.
- Each of the 39 correctness properties maps to exactly one optional backend property test sub-task (mapping listed in the tasks.md Notes).
- Added a Task Dependency Graph of execution waves 0-22.

### Reason
The approved requirements and design needed an actionable, ordered coding plan before implementation starts. The version is bumped once because the header rule of this changelog increments the version whenever requirements.md, design.md, or tasks.md is changed.

### Impact
- Affected requirements: none (all requirements R1-R17 are referenced by at least one task).
- Affected design components: none.
- Affected implementation tasks: tasks.md added (implementation not started).

## v16 - 2026-11-13 - Property 33, version endpoint tags, link schema note, and BaseModel field cleanup

### Changes
Design-only revision (design.md). requirements.md, tasks.md, and the steering files were not modified. No property or endpoint row was renumbered; only Property 33 was edited in the Correctness Properties section.

- **Property 33:** added that a Board invitation specifying a role other than member or admin is rejected with a validation error and Board membership is unchanged; added R10.4 to its Validates line (now 10.1, 10.4, 10.5, 10.8).
- **Endpoint tags:** added R13.6 to the `POST /api/cards/{cardId}/move`, `DELETE /api/cards/{cardId}`, and `DELETE /api/comments/{commentId}` rows (these operations require no `version`).
- **Team_Service:** stated that the join-link create, list, and revoke responses all use the `TeamJoinLink` schema, which includes the server-derived `isExpired` field (computed at read time from `expiresAt`, never stored) alongside `id`, `teamId`, `token`, `status`, `expiresAt`, and `createdAt`.
- **Data Models intro:** stated once that every entity inherits `BaseModel` (id, created_at, updated_at, deleted_at) and that each entity description lists only entity-specific fields; added that `updated_at` and `deleted_at` are not exposed in any response schema except Card's `updatedAt`. Removed the per-entity repetition of the `BaseModel` columns while keeping the Card `updated_at` no-`onupdate` exception (set explicitly) and clarifying Comment's `edited_at` as the user-facing edit timestamp (null until the first edit, set explicitly on edit).
- **Version-checked updates:** stated that a Card edit's conditional `UPDATE` sets `updated_at` and increments `version` explicitly, and a Comment edit's conditional `UPDATE` sets `edited_at` and increments `version` explicitly.
- **API Response Schemas — Team and Board:** removed `updatedAt` from the `Team` and `Board` response shapes so that Card's `updatedAt` is the only base timestamp exposed in any response schema, consistent with the Data Models intro statement above (contract change; `createdAt` is retained on both shapes).

### Reason
Tighten the design to match the finalized DECISIONS: make the R10.4 invalid-role rejection explicit in Property 33, tag the no-version operations with R13.6, remove the duplicated base-column lists in Data Models in favor of a single BaseModel statement, and pin how the version-checked `UPDATE` sets the edit timestamp and bumps `version` for Card and Comment. The `Team`/`Board` `updatedAt` removal resolves an internal contradiction introduced by the Data Models intro statement (updated_at is not exposed in any response schema except Card's `updatedAt`); the two remaining `updatedAt` fields were leftovers and `updated_at` is an internal column, not part of the client contract.

### Impact
- Affected requirements: none (no requirement text changed; refines coverage of R3.3, R4.7, R5.3, R10.4, R13.3, R13.6 and DECISIONS 6, 7, 16).
- Affected design components: Correctness Properties (Property 33), Card_Service and Comment_Service endpoint tables, Team_Service endpoint description, Data Models (intro and all entity field lists), the Version Identifiers and Optimistic Concurrency subsection, and the API Response Schemas `Team` and `Board` shapes.
- Affected implementation tasks: none (tasks.md not created). When the frontend `types/api.ts` is written, the `Team` and `Board` types must omit `updatedAt`.

## v15 - 2026-11-13 - Activity pagination, link schemas, and link-row references refined

### Changes
Design-only revision (design.md). Correctness Properties, requirements.md, tasks.md, and the steering files were not modified. No property or endpoint row was renumbered.

- **Activity_Service:** stated that the `page` query parameter is zero-based (page `0` is the newest page) and that a non-integer `page` returns a `ValidationError`; made explicit that the response shape is `{ items, page, pageSize }` with no `hasMore` or `totalPages`.
- **API Response Schemas — InvitationLink:** reduced to `{ id, boardId, token, status, createdAt }` (removed `createdById` and `updatedAt`).
- **API Response Schemas — TeamJoinLink:** set to `{ id, teamId, token, status, expiresAt, createdAt, isExpired }`, where `isExpired` is derived on the server at read time (`expiresAt` is in the past) and is never stored (removed `createdById` and `updatedAt`; added `teamId` and `isExpired`).
- **Endpoint tables:** the link rows in Access_Control_Service (invitation create/list/revoke) and Team_Service (join-link create/list/revoke) now reference the InvitationLink / TeamJoinLink schemas instead of listing fields inline; the R11.9 and R17.9 tags are preserved.

### Reason
Align the link response shapes with the finalized DECISIONS (server-derived `isExpired` on Team_Join_Links computed from `expiresAt` at read time per DECISION 20; trimmed link payloads) and remove the field-list duplication between the endpoint tables and the API Response Schemas subsection, while pinning the Activity pagination contract (zero-based page, non-integer page is a validation error, fixed `{ items, page, pageSize }` shape).

### Impact
- Affected requirements: none (no requirement text changed; refines the response contract for R8.12/R8.15, R11.1/R11.2/R11.9, R17.1/R17.2/R17.9 and DECISION 20).
- Affected design components: Activity_Service endpoint description, API Response Schemas (InvitationLink, TeamJoinLink), and the link rows in the Access_Control_Service and Team_Service endpoint tables.
- Affected implementation tasks: none (tasks.md not created).

## v14 - 2026-11-13 - API Response Schemas added to API Design

### Changes
Design-only revision (design.md), limited to adding a new "API Response Schemas" subsection at the end of the API Design section. No other section was changed; requirements.md, tasks.md, and the steering files were not modified, and no property or endpoint row was renumbered.

- **Added API Response Schemas subsection** documenting the camelCase response shape for each returned resource: User (identity), Team, TeamMember, TeamJoinLink, TeamJoinLinkPreview, Board (with `teamId` and `currentUserRole`), BoardMember, Column, Card, Comment (flat, with `parentCommentId`), Notification, ActivityEntry, InvitationLink, the analytics response, the Guest board response and Guest comment list, the paginated Notification and Activity responses, and the error envelope.
- Each shape lists camelCase fields with types: UUIDs as strings, timestamps as ISO 8601 UTC strings, nullable fields as `type | null`, and enums with their exact stored values (team roles `team_admin`/`team_regular`; Board roles `admin`/`member`, plus `guest` only in responses; Board status `active`/`archived`; link status `active`/`inactive`; visibility `private`/`team`; Notification status `unread`/`read`; Activity event types). Only keys are camelCased, never values.
- Only fields present in Data Models are used, plus `currentUserRole` and `currentUserTeamRole`. No shape exposes `passwordHash`; `token` appears only on `TeamJoinLink` and `InvitationLink` (the link-issuing endpoints); Guest responses expose Users only as `{ id, displayName }` and never include emails, `version`, or Activity.

### Reason
The API Design section described endpoint behavior and conventions but had no single place defining the exact camelCase response shapes clients and the frontend `types/api.ts` must mirror. The new subsection makes the response contract explicit and traceable to the Data Models and the finalized DECISIONS.

### Impact
- Affected requirements: none (no requirement text changed; the schemas restate the response contract already implied by R1, R6, R8, R9, R10, R11, R15, R16, R17 and the API conventions).
- Affected design components: API Design (new "API Response Schemas" subsection only). No change to Data Models, Error Handling, Correctness Properties, or any other section.
- Affected implementation tasks: none (tasks.md not created).

## v13 - 2026-11-13 - Correctness Properties expanded to 39

### Changes
Design-only revision (design.md), limited to the Correctness Properties section and the one Testing Strategy sentence that counts properties. requirements.md, tasks.md, and the steering files were not modified. No property was renumbered.

- **Rewrote existing properties (numbers and format preserved):**
  - Property 10: cascade now enumerates Columns, Cards, Comments, Notifications, Board memberships, Invitation_Links, and Activity_Entries, and asserts other Boards and all Users and Teams are unchanged (R1.6).
  - Property 16: keyword matched as a literal substring (`%`, `_`, `\` carry no wildcard meaning) and no match yields an empty result; Validates line now R7.1, 7.2, 7.3, 7.4, 7.6.
  - Property 20: scoped to Card and Comment edits (PATCH) as the only version-requiring operations; missing/non-matching version rejected with the resource unchanged, matching version assigns a distinct new version (R13.2, 13.3, 13.5, 14.5).
  - Property 21: removed R5.5 from its Validates line (moved to Property 39); property text unchanged.
  - Property 25: reframed around anonymous Guest access via `/api/guest/{token}/...`, non-GET rejection, and unknown/inactive/revoked/archived-Board rejection, plus generation and revocation isolation; Validates R11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.8.
  - Property 26: stored credential is an argon2 hash (R15.1).
  - Property 28: added email uniqueness and displayName 1–50 after trimming; Validates R15.14, 15.15, 15.16.
  - Property 29: added the logout-revocation clause; Validates R15.8, 15.11, 15.12, 15.13.
- **Added Properties 31–39 (same format):** Teams (31, R16.1–16.5), Board creation with immediate Admin (32, R1.1, 1.11, 1.12), Board invitations (33, R10.1, 10.5, 10.8), Team_Join_Link lifecycle (34, R17.1–17.7), Card move updated_at/version (35, R4.7, 13.6), Activity access (36, R8.14), Board list (37, R1.13), visibility (38, R1.14), Comment ownership (39, R5.5).
- **Testing Strategy:** property count updated from 30 to 39, with a note that Properties 31–34, 37, and 38 run against the transactional test database with small generators.

### Reason
The Correctness Properties section had not yet captured the Teams, Board-creation, Board-invitation, Team_Join_Link, Card-move, Activity-access, Board-list, visibility, and Comment-ownership behaviors already specified in requirements.md and the design body, and several existing properties needed to match the finalized DECISIONS (literal-substring search, version only on Card/Comment PATCH, anonymous Guest endpoints, argon2 hashing, registration validation, logout revocation).

### Impact
- Affected requirements: coverage added/clarified for R1.6, R1.13, R1.14, R4.7, R5.5, R7.4, R8.14, R10.1, R10.5, R10.8, R11.4, R11.6, R11.8, R13.6, R15.1, R15.8, R15.15, R16.1–16.5, R17.1–17.7 (no requirement text changed).
- Affected design components: Correctness Properties (Properties 10, 16, 20, 21, 25, 26, 28, 29 rewritten; 31–39 added) and the Testing Strategy property-count sentence.
- Affected implementation tasks: none (tasks.md not created).

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
