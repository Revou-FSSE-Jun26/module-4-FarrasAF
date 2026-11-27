# Changelog

All notable changes to the task-management-app spec are documented here. Versions are ordered newest-first. The version is bumped each time a spec document (requirements.md, design.md, or tasks.md) is changed.

## v25 - 2026-11-26 - Only Members can be removed from a Board
### Changes
- **Specification changes:** requirements.md Requirement 10 gains 10.10: a removal request for a Board member whose role is Admin (including the requester) is rejected with a validation error and membership stays unchanged, and Board settings shows no remove action for an Admin. 10.6 now covers role changes only, because removal can no longer take away an Admin. 10.2 is unchanged (it already said an Admin removes a Member).
- **Design changes:** design.md Property 23 now covers both rules (role change must keep one Admin; an Admin can never be removed; Validates 10.6 and 10.10) and the `DELETE /api/boards/{boardId}/members/{userId}` row describes the new rule. No data model change.
- **Implementation changes:** `remove_member_service` rejects an Admin with a validation error (the old "last Admin" check is gone because it can no longer apply); `BoardMemberPanel` shows the Remove button only for members whose role is Member; `openapi.yaml` description updated. To remove an Admin, change the role to Member first (role changes are unchanged). Tests updated: `test_access.py` (any Admin rejected, demote-then-remove, API returns 400), Property 23, Property 24, and the role-change API flow.
- **Bug fixes:** none.
- **Breaking changes:** `DELETE /api/boards/{boardId}/members/{userId}` now returns 400 for an Admin member that it used to remove (when another Admin existed).
### Reason
Request that only members, not Admins, can be removed from a Board. Admins stay manageable through the existing role change.
### Impact
- Affected requirements: 10.6 narrowed, 10.10 added.
- Affected design components: Property 23, Access_Control_Service endpoint table.
- Affected implementation tasks: 8.1 and 8.4 text and requirement references updated; mapping row R10.10 added. Unit, property, and API tests changed.

## v24 - 2026-11-26 - Board progress bar
### Changes
- **Specification changes:** requirements.md gains Requirement 21 (criteria 21.1 to 21.6): a progress bar at the top right of the Board view, in the Board title row, showing Cards in Columns named exactly "Done" divided by all Cards as a rounded whole percent (6 of 10 shows 60%); all "Done" Columns count together (as in R9.3); 0% for a Board with no Cards; it follows Card and Column changes; computed from the loaded Board with no separate request; stacks without overlap below 1024px. Requirements 1 to 20 are unchanged.
- **Design changes:** design.md Frontend Structure gains a "Board progress bar (R21)" bullet. No endpoint, data model, or property change.
- **Implementation changes:** new `lib/boardProgress.ts`, `components/board/BoardProgress.tsx`, and shared `components/shared/BaseProgressBar.tsx` (the Card to-do progress `ChecklistProgress` now uses it, with the same look); the `BoardView` header row was restructured so the bar sits level with the title. Task 15.9 added (completed), wave 119 appended, mapping rows R21.1 to R21.6.
- **Bug fixes:** none.
- **Breaking changes:** none.
### Reason
Request for a Board-level progress bar based on the share of Cards in the "Done" Column. Choices that follow existing rules: the "Done" match and multi-Column counting follow Analytics (R9.3), and rounding follows the Card to-do bar (R20.11).
### Impact
- Affected requirements: Requirement 21 added.
- Affected design components: Frontend Structure.
- Affected implementation tasks: 15.9 added. No E2E test written for this flow; task 19 stays open.

## v23 - 2026-11-26 - Card to-do list and progress bar
### Changes
- **Specification changes:** requirements.md gains Requirement 20 (criteria 20.1 to 20.11) and the glossary term "To-do item": one to-do list per Card; Members and Admins add (text 1 to 255 after trimming, at most 50 items, appended last), edit the text, tick and untick, and delete items; item changes do not change the Card's version or Updated timestamp and create no Activity_Entry or Notification; Guests see the list read-only; the Card details show a progress bar at the top right in the Title row (done items divided by all items, rounded to a whole percent, hidden when there are no items). Requirements 1 to 19 are unchanged.
- **Steering change:** `product.md` no longer lists "checklists" under the V1 Non-Goals and lists the to-do list under Core Features (approved by the user).
- **Design changes:** design.md gains the `ChecklistItem` entity, three endpoints (`POST /api/cards/{cardId}/checklist-items`, `PATCH` and `DELETE /api/checklist-items/{itemId}`), the `ChecklistItem` response schema, `checklistItems` on the Card and Guest board schemas, the service table row, and a Frontend Structure bullet. No new property: the to-do rules are covered by unit and API tests.
- **Implementation changes:** new table `checklist_items` (migration `d5e6f7a8b9c0`), `checklist/` backend module, RBAC resolution for `item_id` routes in `rbac.py`, `checklistItems` embedded in Card and Guest responses, `openapi.yaml` updated, frontend types, API client methods, `lib/checklist.ts`, `useChecklist`, and the `ChecklistProgress`, `ChecklistSection`, and `ChecklistItemRow` components. Tasks 6.5 and 15.8 added (completed), waves 117 and 118 appended, mapping rows R20.1 to R20.11.
- **Bug fixes:** none.
- **Breaking changes:** none. Card and Guest card responses gain a `checklistItems` array.
### Reason
Request to add a to-do list to Card details with a progress bar. Decisions confirmed with the user: one list per card, add/edit/tick/untick/delete without reordering, limits of 255 characters and 50 items, only Members and Admins can change items, no concurrency check and no Activity entries for item changes, progress on the Card details only, and no change to Notifications or search.
### Impact
- Affected requirements: Requirement 20 added; glossary updated.
- Affected design components: Service table, Data Models, API Design (Card_Service table and response schemas), Frontend Structure.
- Affected implementation tasks: 6.5 and 15.8 added. The Playwright E2E test for this flow is not written yet; task 19 stays open (see also 19.11).

## v22 - 2026-11-26 - Activity sentences with the user name and event details
### Changes
- **Specification changes:** requirements.md Requirement 8 gains 8.16 (store the names needed for the sentence with each Activity_Entry, return the actor's display name and those names, none for older entries) and 8.17 (show a sentence starting with the user's display name, for example `Ada moved the card "Fix login" from "To Do" to "Doing"`). 8.1 to 8.15 are unchanged.
- **Design changes:** design.md ActivityEntry data model gains the nullable `details` JSON column; the ActivityEntry response schema now matches what the API sends (`actor: { id, displayName }`, `details`; the earlier `boardId` and `actorId` were never returned) and lists the `details` keys per event type.
- **Implementation changes:** new migration `c4d5e6f7a8b9` adds `activity_entries.details`; `record_activity` accepts `details`; the cards, columns, comments, and access services save the names in the same transaction; `openapi.yaml` updated; frontend `ActivityEntry` type, `lib/activityText.ts`, `ActivityView`, and `useActivity` changed. Tasks 6.4 and 15.7 added (completed), waves 115 and 116 appended, mapping rows R8.16 and R8.17.
- **Bug fixes:** the Activity page showed "Unknown user" for every entry because the frontend read `actorId`, which the API never sent (it sends `actor`). The name now comes from `actor.displayName`.
- **Breaking changes:** the ActivityEntry response shape in the design document changed to match the real API; the actual API response only gains `details`.
### Reason
Request to show the real user name on the Activity page and to describe each event in a full sentence. Decisions confirmed with the user: show the user name only, use the proposed wording per event, and add a `details` column with a migration.
### Impact
- Affected requirements: 8.16 and 8.17 added.
- Affected design components: Data Models (ActivityEntry), API Response Schemas (ActivityEntry).
- Affected implementation tasks: 6.4 and 15.7 added.
- Existing Activity entries have no details and show the shorter sentence (for example `Ada moved the card`).

## v21 - 2026-11-26 - Board sidebar navigation and in-Board Card search
### Changes
- **Specification changes:** requirements.md gains Requirement 19 (criteria 19.1 to 19.9): a sidebar on the four Board pages (Board, Activity, Analytics, Board settings) with the current page marked, the Activity, Analytics, and Board settings links moved out of the Board view header into the sidebar, and a sidebar search field that lists the Cards of that Board whose Title contains the typed text (trimmed, case-insensitive substring) after every keystroke, shows Title and Column name, opens the Card on selection, shows a no-match message, and stacks above the content below 1024px. Requirements 1 to 18 are unchanged.
- **Design changes:** design.md Frontend Structure gains a "Board sidebar and in-Board search (R19)" bullet: Board `layout.tsx`, `BoardProvider` (one `useBoard` call shared through context), `BoardShell`, `BoardSidebar`, and the pure `filterCardsByTitle` helper. Search runs in the browser on the loaded Board; no endpoint, API type, or dependency is added.
- **Implementation changes:** task 15.6 (completed) and 19.11 (E2E, not started) added; parent task 19 reopened; two waves (113, 114) appended to the dependency graph so earlier wave numbers stay unchanged; the Requirement-to-Task Mapping gains R19.1 to R19.9.
- **Bug fixes:** none (the "Create Board" and "Create Team" button alignment and the RevoTask header name and logo were cosmetic implementation changes and need no spec version).
- **Breaking changes:** none.
### Reason
Request for a left sidebar on the Board pages like a project sidebar, holding Activity, Analytics, and Board settings plus a live search of that Board's Cards. Decisions: the sidebar appears on all four Board pages, results are a list in the sidebar (the Board columns are not filtered), and matching is client-side because the Board's Cards are already loaded.
### Impact
- Affected requirements: Requirement 19 added.
- Affected design components: Frontend Structure.
- Affected implementation tasks: 15.6 added, 19.11 added, 19 reopened; mapping rows R19.1 to R19.9.

## v20 - 2026-11-20 - User profile (display name and password)
### Changes
- **Specification changes:** requirements.md gains Requirement 18 (User Profile, criteria 18.1 to 18.11): view the Profile, edit the display name (1 to 50 characters after trimming), reject any other Profile field including the email, show the new name in later responses, change the password with the current password (new password at least 8 characters and different, all refresh tokens revoked, new cookies issued, failure count reset), count a wrong current password toward the existing lockout, give a locked account the same error as a wrong password, and provide a `/profile` page. Added the "Profile" glossary term and updated the Introduction (Profile page added; changing the email address added to the V1 exclusions). Requirements 1 to 17 are unchanged and not renumbered.
- **Design changes:** design.md adds `PATCH /api/auth/me` and `POST /api/auth/me/password` to Authentication_Service (now R15, R18), a Profile paragraph (order of checks, lockout sharing, token revocation and re-issue, `400` not `401` for a wrong current password), the `/profile` page in Frontend Structure, the User entity note (no new columns), the error-table and security entries, and Property 40 (total 40 properties; Property 40 runs against the test database).
- **Implementation changes:** none yet. Tasks 4.10, 4.11, 4.12, 15.5, 19.10, and 20.5 are added as not started.
- **Bug fixes:** none.
- **Breaking changes:** none. Existing endpoints and responses are unchanged.
### Reason
The spec had no way for a User to edit their own account details. Decisions confirmed with the user: scope is display name and password change; the email stays read-only because V1 has no email verification.
### Impact
- Affected requirements: Requirement 18 added; Introduction and Glossary updated.
- Affected design components: Authentication_Service, Frontend Structure, Data Models (User note), Error Handling, Security Considerations, Correctness Properties (Property 40), Testing Strategy.
- Affected implementation tasks: added 4.10 to 4.12 (auth module, unit tests, Property 40 test), 15.5 (profile page), 19.10 (Profile E2E), 20.5 (OpenAPI update, 50 operations); parent tasks 4 and 15 were reopened because they now contain unfinished sub-tasks; waves in the dependency graph renumbered (113 waves); the Requirement-to-Task and Property-to-Task mappings gain R18.1 to R18.11 and P40.
- Steering files were not edited. `product.md` lists no profile feature and its Non-Goals do not mention changing the email address.

## v19 - 2026-11-18 - Frontend error handling, toasts, and error boundaries
### Changes
- **Specification changes:** requirements.md Requirement 14 gains criteria 14.6 (failed actions show a toast), 14.7 (4xx shows the server message; 5xx, network, and unexpected failures show a fixed generic message), 14.8 (fallback page for unexpected rendering errors), and 14.9 (no stack traces, digests, error codes, debug output, or console error output in production).
- **Design changes:** added an "Error handling and toasts" bullet to Frontend Structure in design.md (error helper, toast provider, error boundaries, which errors become toasts).
- **Implementation changes:** added `src/lib/errorHandler.ts`, `src/hooks/useToast.ts`, `BaseToastProvider`, `BaseErrorFallback`, `app/error.tsx`, `app/(app)/error.tsx`, `app/global-error.tsx`, and `app/not-found.tsx`; mounted the provider in the root layout; changed `BaseToast` to be positioned by its container. Hooks and forms now report failures through `useToast`; removed the `actionError` state from `useBoard`, `useBoardSettings`, and `useTeamDetail`, the `onMoveError` parameter of `useDragAndDrop`, the `error` field of `useCardDetail`, and the `actionError` props of `BoardMemberPanel` and `JoinLinkPanel`.
- **Bug fixes:** `CreateBoardForm` and `CreateTeamForm` no longer show a raw `Error.message` (for example "Failed to fetch") to the user.
- **Breaking changes:** none to the API. Failed actions that previously showed inline text (Board settings members, Team join links, Card detail, Comments server errors, Board actions) now show a toast.
### Reason
Request to add error boundaries and a central error handler on the frontend, show errors through toasts, and make sure no debug output is visible in production. Decisions confirmed with the user: action and background errors become toasts while page-load failures keep their error view and also toast and field validation stays inline; 4xx errors show the server message and everything else shows a generic message; dev details go to the browser console only.
### Impact
- Affected requirements: 14.6, 14.7, 14.8, 14.9 added; 15.3 unchanged (login keeps its generic inline message for 4xx responses).
- Affected design components: Frontend Structure.
- Affected implementation tasks: 15.4 added (completed) and wave 82 in the dependency graph (later waves renumbered by one); the Requirement-to-Task Mapping gains R14.6 to R14.9 and R15.3 now lists 15.4.
- Bug fix (implementation only, no spec change): `next build` failed while prerendering `/invite/[token]` because `params` was read outside `<Suspense>` with `cacheComponents` enabled. The page is now a server component that awaits `params` inside a `<Suspense>` boundary with a loading fallback, like `/join/[token]`. `GuestBoardView` and its behavior are unchanged. `next build` now succeeds, which unblocks the build step of task 18.1.
## v18 - 2026-11-18 - API documentation (OpenAPI and Swagger UI)

### Changes
- **Specification changes:** none to requirements.md (the documentation is development tooling, not product behavior, so no requirement R1-R17 was added or changed).
- **Design changes:** added an "API Documentation (OpenAPI / Swagger UI)" subsection to the API Design section of design.md, and a note in the public-endpoint list that two development-only documentation routes exist.
- **Implementation changes:** added `backend/openapi.yaml` (48 operations, every route in the app), `backend/flask_app/common/docs.py` (`GET /api/docs`, `GET /api/docs/openapi.yaml`), the `API_DOCS_ENABLED` config key (true only when `APP_ENV=development`), and the conditional `docs_bp` registration in `app.py`. Swagger UI is loaded from a CDN, so no dependency was added.
- **Tasks:** added task 20.4 (completed) and wave 104 in the dependency graph.
- **Bug fixes / breaking changes:** none.

### Reason
Request for API docs using Swagger. Decisions confirmed with the user: serve Swagger UI from the app, enable it only in development, document every endpoint including Guest routes, and record the change as a new version.

### Impact
- Affected requirements: none.
- Affected design components: API Design (new API Documentation subsection, public-endpoint list note).
- Affected implementation tasks: 20.4 added; no existing task changed.
- Note: the two docs routes are public, which `structure.md` and `backend.md` rule 2 treat as an exception requiring approval. The user approved this on 2026-11-18; the steering files were not edited.

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
