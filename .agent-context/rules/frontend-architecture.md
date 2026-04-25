# Frontend Design and Interaction Boundaries

UI work must load the smallest relevant surface, not the entire engineering handbook.

## Auto Activation
When the request is UI-facing, this rule activates automatically.

UI scope triggers:
- ui, ux, page, screen, component, layout, landing, dashboard, form, onboarding, animation, interaction
- redesign, reskin, visual refresh, responsive fix, hierarchy fix
- frontend deliverables even when the task also touches backend code

## What This Rule Is For
Use this file to enforce:
- anti-generic layout and morphology boundaries
- responsive mutation requirements
- accessibility floor for expressive UI
- source hygiene for visual decisions
- lightweight implementation boundaries that keep UI code from collapsing into framework defaults

Do not use this file to teach generic frontend basics the model already knows.

## Source Hygiene and Source Boundaries

- Valid style context is limited to current repo evidence, the active brief, and current project docs.
- This rule guides the LLM; it must not choose the final style, framework, palette, typography, layout paradigm, or animation library offline.
- Design continuity is opt-in. If the user does not request continuity, synthesize from the current product context instead of remembered layouts.
- Repo evidence outranks memory residue every time.
- External references are tainted by default. If the user supplies one, convert only explicit constraints into the current contract and do not compare against or imitate the source surface.
- If a new UI, animation, styling, or component library is needed, research current official docs and choose the latest stable compatible option for the project.

## Zero-Based Redesign Boundary

- If the user asks for a redesign "from zero" or equivalent reset language, treat existing UI as behavioral/content evidence only, not as visual direction.
- Do not preserve prior palette, typography, hero composition, navigation placement, component morphology, motion signature, or image framing unless the user explicitly requests continuity.
- The new UI must materially recompose at least the primary surface, content hierarchy, interaction model, and responsive information architecture.
- A dark-mode flip, same layout with different colors, or restyled version of the previous hero is not a zero-based redesign.
- Record the visual reset in `docs/DESIGN.md` and `docs/design-intent.json` before coding.

## Accessibility Split

- Treat WCAG 2.2 AA as the hard compliance floor.
- Treat APCA as advisory perceptual tuning only.
- Hard checks must include focus visibility, focus appearance, target size, keyboard access, accessible authentication, use-of-color-only failures, and dynamic status/state access.
- Fix the violation without flattening the interface into generic safe chrome unless that is the only safe option.

## Anti-Generic UI Boundaries

- Do not default to interchangeable dashboard chrome, balanced card grids, centered marketing shells, or generic component-kit surfaces unless the product explicitly needs them.
- Do not let repeated surfaces share the same visual treatment by habit. Repetition is allowed only when the contract explains the product reason.
- Do not use default framework button and input treatment as the final UI language.
- Do not let heading, body, and data/meta roles collapse into one safe typographic family without explicit rationale.
- At least one visual, interaction, content, motion, or state behavior must read as project-specific at a glance.

## Dynamic Avant-Garde Anchor Boundary

- If the user gives no current-task visual research or reference, the scaffold, old UI, and existing design docs do not count as research.
- Before UI code, choose one agent-synthesized conceptual anchor from high-variance non-software domains and record only the final anchor in `docs/design-intent.json`.
- Internally reject the safest dashboard, portal, card-grid, admin-shell, or minimalist-web-app mental model before writing CSS.
- Typography, spacing, morphology, motion, and responsive recomposition must derive from the chosen anchor, not from framework defaults.
- Default to an expressive motion plan derived from the anchor. Use spatial transitions, micro-interactions, scroll choreography, and modern animation libraries when they improve the experience; include reduced-motion and performance safeguards without using them as an excuse for a static UI.

## Responsive Mutation Requirements

- Responsive quality is not allowed to be scale-only. At least one surface must materially change position, grouping, priority, or disclosure strategy between mobile and desktop.
- Mobile must prioritize the first decisive action, not preserve desktop balance out of habit.
- Tablet must simplify simultaneous surfaces without becoming a shrunken desktop.
- Desktop may expose more context, but it must not become an interchangeable admin shell by default.

## Surface and Morphology Requirements

- Define the primary user task or reading path from current evidence before arranging surfaces.
- Supporting surfaces must earn their placement through role, priority, or behavior. They must not feel like cloned modules.
- Component states must preserve identity under hover, focus, loading, success, empty, and error. Do not let everything collapse into anonymous rounded panels.
- Motion should be expressive by default for modern UI work. Make it strengthen hierarchy, feedback, or memorability, then keep it reduced-motion-safe and performant.

## Implementation Boundaries

- Follow the shipped project stack and current repo patterns before inventing state-management or data-fetching rules.
- Do not hardcode Zustand, React Query, smart/dumb component doctrine, or any framework-specific architecture as universal frontend law in baseline design governance.
- If the repo already uses a runtime pattern, stay consistent with it. If it does not, choose the lightest modern fit for the task and document why.
- Keep structure feature-oriented and avoid giant catch-all UI buckets when the repo does not explicitly require them.
