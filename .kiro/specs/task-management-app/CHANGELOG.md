# Changelog

All notable changes to the task-management-app spec are documented here. Versions are ordered newest-first. The version is bumped each time a spec document (requirements.md, design.md, or tasks.md) is changed.

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
