---
inclusion: fileMatch
fileMatchPattern: "frontend/**/*.{ts,tsx}"
---

# Frontend Guidelines (Next.js + React + TypeScript + Tailwind)

## Naming Conventions

### 1. Component files
**Rule:** Component files are PascalCase with a .tsx extension
**Rationale:** PascalCase follows React component naming conventions and makes component files easy to identify. The .tsx extension indicates that the file contains JSX with TypeScript.
**Example:** CardDetailModal.tsx, NotificationBell.tsx, SearchBar.tsx

### 2. Custom hook files
**Rule:** Hook files are camelCase with prefix "use"
**Rationale:** React requires custom hooks to start with use to follow the Rules of Hooks and make them recognizable as hook functions. camelCase keeps naming consistent with JavaScript function conventions.
**Example:** useDragAndDrop.ts, useNotifications.ts

### 3. Props interfaces
**Rule:** A props interface is the component name + "Props". Domain types (Board, Column, Card, Comment) are imported from `@/types/api`.
**Rationale:** This naming convention clearly associates an interface with its component, improves code readability, and makes component props easier to identify and maintain.
**Example:** `interface BoardListItemProps { board: Board }` for BoardListItem.tsx,
`interface CardItemProps { card: Card }` for CardItem.tsx

### 4. Event handler props
**Rule:** Callback props are named on + Event using PascalCase
**Rationale:** The on prefix distinguishes event callback props from regular props and follows React's event naming conventions. It makes component APIs predictable and easier to understand.
**Example:** <CardItem onCardMove={handleMove} onCardDelete={remove} />

### 5. Next.js page files
**Rule:** A route is a folder with page.tsx; the component is named for the page
**Rationale:** Next.js App Router uses file-system-based routing, where page.tsx defines the UI for a route. Naming the component descriptively improves readability and makes page components easier to identify.
**Example:** src/app/boards/page.tsx (BoardsPage), src/app/boards/[boardId]/page.tsx (BoardDetailPage)

### 6. Boolean props
**Rule:** Boolean props use an is/has prefix
**Rationale:** The is and has prefixes make boolean values immediately recognizable and allow conditions to read naturally, improving code readability
**Example:** isLoading, hasError

### 7. Tailwind classes
**Rule:** Class order is enforced by prettier-plugin-tailwindcss; do not reorder manually.
**Rationale:** A consistent class ordering makes JSX easier to scan, reduces visual clutter, and helps developers quickly locate and modify specific styling properties.
**Example:** className="flex items-center gap-4 p-4 w-full text-sm font-medium text-gray-900 hover:bg-gray-100"

### 8. Shared primitives
**Rule:** Shared primitive components use a Base prefix and are located in src/components/shared/
**Rationale:** The Base prefix distinguishes reusable UI primitives from feature-specific components. Keeping them in a shared directory promotes reusability, consistency, and centralized maintenance across the application.
**Example:** src/components/shared/BaseButton.tsx, src/components/shared/BaseInput.tsx, src/components/shared/BaseModal.tsx

## TypeScript Rules

### 9. No `any`
**Rule:** Never use `any`, explicit or implicit. Use `unknown` with type narrowing, generics, or a proper interface. Do not silence errors with `@ts-ignore` or `as any`.
**Rationale:** `any` disables type checking and hides bugs that the compiler would otherwise catch. The project runs in strict mode, so untyped code fails lint and type checks.
**Example:** `const data: unknown = await res.json();` then narrow it, instead of `const data: any = await res.json();`

### 10. API types come from one place
**Rule:** All API request and response types live in `src/types/api.ts` and mirror the data models and endpoints in `design.md`. Import them with `@/types/api`; never redefine them inline in components or hooks. If `src/types/api.ts` does not yet contain a needed type, add it there first. All fields are camelCase, matching the JSON API (e.g. `orderIndex`, `createdAt`, `assigneeId`); never use snake_case in frontend code.
**Rationale:** A single source of truth keeps the frontend aligned with the backend contract and gives generated code real types to use instead of falling back to `any`.
**Example:** `import type { Card, Column } from '@/types/api';`

### 11. Explicit types at boundaries
**Rule:** Explicitly type component props, hook parameters, and hook return values. Type `useState` and `useRef` when the initial value does not make the type obvious (empty arrays, `null`). Use `import type` for type-only imports.
**Rationale:** Empty initial values are inferred as `never[]` or `null`, which causes implicit-type errors. Explicit boundaries keep the code readable.
**Example:** `const [cards, setCards] = useState<Card[]>([]);`

## Data & State

### 12. One API client
**Rule:** All HTTP calls go through the typed client in `src/lib/apiClient.ts`; no raw `fetch` in components or hooks. The client calls same-origin `/api/...` paths (proxied to the backend by Next.js rewrites), never the backend URL. Authentication relies on `HttpOnly` cookies the browser sends automatically: the client never reads, stores, or attaches tokens, and nothing is ever put in `localStorage`, `sessionStorage`, or a JS-readable cookie. On a `401`, call the refresh endpoint once and retry the original request; if refresh fails, redirect to `/login`, except on public pages (`/login`, `/register`), where the error is shown instead. Errors are typed to match the envelope in `design.md`. Do not attempt a refresh for the auth endpoints themselves (login, register, refresh); a `401` there is returned to the caller as a normal error. 
**Rationale:** Cookies keep tokens out of reach of XSS, and one client keeps refresh and error handling in one place.
**Example:** `const card = await apiClient.moveCard(cardId, { targetColumnId, targetIndex });`

### 13. Logic in hooks, UI in components
**Rule:** Components render UI only. Data fetching, mutations, polling, and drag-and-drop logic live in custom hooks in `src/hooks/`. Pure helpers (such as target-index calculation) go in `src/lib/` and take no React dependencies.
**Rationale:** Separating logic from UI keeps components small and makes the logic easier to change and reuse.
**Example:** `useDragAndDrop` computes the target Column and index; `BoardView` only renders.

### 14. Polling, not WebSockets
**Rule:** Notifications are fetched by HTTP polling through `useNotifications`. Each poll requests the newest page without a cursor; the `nextCursor` from a response is used only to load older pages on demand. Do not add WebSockets or server-sent events.
**Rationale:** Real-time collaboration is a V1 non-goal (see `product.md`), and the cursor pages toward older Notifications (R6).
**Example:** `useNotifications` polls `GET /api/notifications` on an interval; a "Load more" button requests `GET /api/notifications?cursor=<nextCursor>`.

### 15. Optimistic updates reconcile with the server
**Rule:** Drag-and-drop may update the UI optimistically, but the server response is authoritative. On error, roll back to the previous state and show a clear message. Send the resource `version` on every Card or Comment update and handle a `409` conflict by refetching and informing the user.
**Rationale:** The server owns ordering and concurrency (R4, R13); the UI must not drift from it.
**Example:** On a failed `moveCard`, restore the previous Column state and show an error toast.

## UX & Testing

### 16. Always handle loading, empty, and error states
**Rule:** Every data-driven view renders a loading state, an empty state, and an error state, not just the success case.
**Rationale:** Real users hit all four states, and missing states are the most common visible bug in generated UI.
**Example:** A Column with no Cards shows "No cards yet" and an add-Card button.

### 17. Responsive layout
**Rule:** At widths of 1024px and above, all Columns, Cards, and primary navigation are reachable without horizontal page scrolling. Below 1024px, controls stay visible and operable with no overlapping content. Use Tailwind breakpoints (`lg:` for 1024px).
**Rationale:** Required by the non-functional requirements (R14.3, R14.4).
**Example:** `className="flex flex-col lg:flex-row"`

### 18. Role-aware UI
**Rule:** Hide or disable controls the current user's role cannot use. The Board role comes from the `currentUserRole` field on the Board response (`admin`, `member`, or `guest`), and the Team role comes from the `currentUserTeamRole` field on the Team response; both are typed in `src/types/api.ts`. `GET /api/auth/me` returns identity only (id, email, display name). Never decode tokens in the browser and never infer a role from other data. Guest pages (`/invite/[token]`) are read-only and render no write controls. Roles are read from the server on every fetch, so refetch the Board or Team after an action that changes membership. The UI check is for convenience only; the backend remains the authority.
**Rationale:** Roles are resolved from stored membership on each request (R12.1), so the response is the single reliable source, and the matrix in `design.md` is not duplicated in the client.
**Example:** The "Add column" button renders only when `board.currentUserRole === 'admin'`; the "Create join link" button renders only when `team.currentUserTeamRole` is the Team_Admin value.

### 19. Playwright E2E tests
**Rule:** Key user flows are covered by Playwright tests in `frontend/e2e/<flow>.spec.ts`: authentication, Board/Column/Card CRUD, drag-and-drop, comments and mentions, search, and Guest access via an Invitation Link. Locate elements with `getByRole`, `getByLabel`, or `getByText` first. Add a `data-testid` only when no accessible locator works (for example, draggable Cards).
**Rationale:** E2E tests verify real behavior from the user's side, and accessible locators also keep the UI accessible.
**Example:** `await page.getByRole('button', { name: 'Add card' }).click();`

### 20. Independent E2E tests
**Rule:** Each test sets up its own data (via the seed script or API calls) and does not depend on another test's data or run order. Do not use fixed waits such as `waitForTimeout`; rely on Playwright's auto-waiting and `expect` assertions.
**Rationale:** Dependent or timing-based tests are flaky and fail unpredictably.
**Example:** `await expect(page.getByText('Card created')).toBeVisible();`

### 21. Client components
**Rule:** Any file that uses hooks, state, effects, or event handlers starts with `'use client'`. Data fetching happens in client components through hooks that call `apiClient`; do not fetch from server components, because the browser's cookies are not available there.
**Rationale:** Missing `'use client'` is the most common App Router error, and server-side fetches would not carry the user's cookies.
**Example:** `'use client';` as the first line of `BoardView.tsx`.

### 22. No raw HTML injection
**Rule:** Render user content (Titles, Descriptions, Comments) as plain text. Never use `dangerouslySetInnerHTML`.
**Rationale:** `HttpOnly` cookies reduce the impact of XSS but do not replace escaping user content.
**Example:** `<p>{comment.body}</p>`