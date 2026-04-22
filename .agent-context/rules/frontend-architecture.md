# Frontend Architecture & Composition Patterns

> A complex UI is built from simple, mathematically robust functions. State is dangerous; isolate it.

## 0. Frontend Designer Mode (Auto Activation)
When the user request is UI-facing, frontend design governance activates automatically. No manual mode toggle is required.

UI scope trigger signals (any one is enough):
- keywords such as: ui, ux, page, screen, component, layout, landing, dashboard, form, onboarding, animation, interaction
- explicit requests to improve visual quality, conversion clarity, or interaction behavior
- feature requests that include frontend deliverables even when backend changes are also included

Mandatory behavior when triggered:
- apply consolidated review checks from `.agent-context/review-checklists/pr-checklist.md`
- apply structural checks from `.agent-context/review-checklists/architecture-review.md`
- score and review generated UI work against visual intent, interaction quality, and conversion clarity
- reject template-only repetitive outputs and force a distinct layout direction
- treat prior website memory or old-project visual carryover as invalid evidence unless the user explicitly requests continuity with that exact system
- do not flatten ambitious visual or motion ideas by default; keep them when they are optimized, intentional, and accessible

## UI Consistency Guardrails (Mandatory)

- Content language must stay consistent per screen and flow unless user requests multilingual output.
- Text color must remain contrast-safe against its background; no color collisions.
- Layout must avoid overlap, clipped text, and misaligned key actions across breakpoints.
- Responsive quality requires layout mutation and task reprioritization across breakpoints. Shrinking the desktop layout is not enough.
- Keep spacing and positioning token-driven so repeated outputs stay stable.
- Distinctive visual direction is allowed. Originality is a quality signal when hierarchy, task clarity, and accessibility still hold.
- Motion is allowed to be expressive. Judge it by clarity, reduced-motion safety, and rendering cost, not by how restrained it looks.
- Prefer transform and opacity for rich motion. Treat layout-thrashing animation, uncontrolled autoplay, and heavy continuous effects as optimization problems to solve, not reasons to remove personality from the UI entirely.

## 1. File Structure (Feature-Driven Design)
Organize your application by feature domain, not by file type.
- **BANNED:** Monolithic directories like `/components` (with 500 files), `/hooks`, `/api`.
- **REQUIRED (Feature Sliced):**
  ```
  src/
    features/
      authentication/
        api/          #(login, logout fetchers)
        components/   #(LoginForm, ProfileView)
        hooks/        #(useAuth, useSession)
        store.ts      #(Zustand slice)
        types.ts      #(Zod schemas)
    components/       #(Global shared UI like Button, Modal)
    lib/              #(Axios instance, utility wrappers)
  ```

## 2. Separation of State and UI (Smart vs. Dumb)
- **Dumb Components (Presentational):** Receive data via `props`, emit events via callbacks (`onAction`). They do not know about the network, global context, or databases.
- **Smart Components (Containers):** Connect to global state (Redux/Zustand), fetch data (React Query), and pass it down.
- **Rule:** An intricate UI layout component should NEVER contain a `fetch` or `useQuery` call.

## 3. Server State vs. Client State
Modern frontend frameworks differentiate between remote and local data.
- **Server State (Async, Cached):** Data belonging to the database. MUST be managed by tools like `TanStack Query` (React Query) or `SWR`.
- **Client State (Sync, Ephemeral):** UI toggles, modal states, form drafts. Manage via `useState`, `useContext`, or `Zustand`.
- **BANNED:** Storing API responses in a global Redux/Zustand store (e.g., `dispatch(setUsers(data))`). Use React Query instead.

## 4. The Composition Pattern (Avoiding Prop Drilling)
If a component takes more than 5 props, or if props are passed down through 3+ intermediate components, the architecture is broken.
- **BANNED:** `<Layout user={user} theme={theme} onLogout={handleLogout} />`
- **REQUIRED:** Use React's `children` prop and composition.
  ```tsx
  // ✅ Clean composition
  <Layout>
    <Sidebar user={user} />
    <Content onLogout={handleLogout} />
  </Layout>
  ```

## 5. Explicit Component Contracts (Typing)
Every component **MUST** have an explicit, exported interface for its props.
- **BANNED:** `const Button = (props: any) => ...`
- **REQUIRED:** Prefix handlers with `on` and booleans with `is/has`.
  ```typescript
  export interface ButtonProps {
    variant: 'primary' | 'secondary';
    isLoading?: boolean;
    onClick: () => void;
    children: React.ReactNode;
  }
  ```

## 6. Form Handling & Validation
Never write manual state bindings for complex forms.
- **Rule:** All forms MUST use a robust library (`react-hook-form` is the standard) combined with a schema validator (`Zod`).
- **BANNED:** Creating 5 `useState` variables for 5 input fields.

## 7. Performance & Re-renders
React is fast until you break it.
- **Rule:** Do not pass newly instantiated objects or arrow functions directly into dependency arrays (`useEffect`) or memoized components (`React.memo`) unless wrapped in `useMemo`/`useCallback`.
- **Rule:** Never execute expensive mapping/filtering inside the render path blindly without memoization.
