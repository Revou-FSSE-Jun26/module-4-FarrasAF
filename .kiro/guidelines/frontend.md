---
inclusion: manual
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
**Rule:** A props interface is the component name + "Props"
**Rationale:** This naming convention clearly associates an interface with its component, improves code readability, and makes component props easier to identify and maintain.
**Example:** interface BoardCardProps { board: Board }

### 4. Event handler props
**Rule:** Callback props are named on + Event using PascalCase
**Rationale:** The on prefix distinguishes event callback props from regular props and follows React's event naming conventions. It makes component APIs predictable and easier to understand.
**Example:** <CardItem onCardMove={handleMove} onCardDelete={remove} />

### 5. Next.js page files
**Rule:** A route is a folder with page.tsx; the component is named for the page
**Rationale:** Next.js App Router uses file-system-based routing, where page.tsx defines the UI for a route. Naming the component descriptively improves readability and makes page components easier to identify.
**Example:** app/boards/page.tsx (BoardsPage), app/boards/[id]/page.tsx (BoardDetailPage)

### 6. Boolean props
**Rule:** Boolean props use an is/has prefix
**Rationale:** The is and has prefixes make boolean values immediately recognizable and allow conditions to read naturally, improving code readability
**Example:** isLoading, hasError

### 7. Tailwind classes
**Rule:** Organize Tailwind classes in this order: layout -> spacing -> sizing -> typography -> color -> interactive
**Rationale:** A consistent class ordering makes JSX easier to scan, reduces visual clutter, and helps developers quickly locate and modify specific styling properties.
**Example:** className="flex items-center gap-4 p-4 w-full text-sm font-medium text-gray-900 hover:bg-gray-100"

### 8. Shared primitives
**Rule:** Shared primitive components use a Base prefix and are located in components/shared/
**Rationale:** The Base prefix distinguishes reusable UI primitives from feature-specific components. Keeping them in a shared directory promotes reusability, consistency, and centralized maintenance across the application.
**Example:** components/shared/BaseButton.tsx, components/shared/BaseInput.tsx, components/shared/BaseModal.tsx