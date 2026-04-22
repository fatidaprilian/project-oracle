
# Bootstrap Dynamic Design Contract

When a user requests frontend design or redesign, the agent should automatically synthesize a dynamic design contract made of:
- `docs/DESIGN.md` for human-readable design direction and implementation rationale
- `docs/design-intent.json` for machine-readable intent, anti-generic constraints, and validation hints

This contract is a structure and reasoning system, not a fixed visual template. It must adapt to product context, user needs, platform constraints, and current design signals.

UI Design Mode is context-isolated by default:
- Load [AGENTS.md](../../AGENTS.md), [frontend-architecture.md](../rules/frontend-architecture.md), this prompt, UI-relevant state files, current UI code, and existing design docs first.
- Do not eagerly load backend-only rules such as [database-design.md](../rules/database-design.md), [docker-runtime.md](../rules/docker-runtime.md), or [microservices.md](../rules/microservices.md) unless the task explicitly crosses those boundaries.
- Treat UI consistency, accessibility, and cross-viewport adaptation as first-class constraints, not cosmetic afterthoughts.
- Start the visual language from the current project context, not from prior website references or remembered layouts from earlier chats.

The agent must:
1. Read [AGENTS.md](../../AGENTS.md) for project context and team roles.
2. Read [frontend-architecture.md](../rules/frontend-architecture.md) and apply its UI consistency guardrails.
3. Use repository evidence from [.agent-context/state/onboarding-report.json](../state/onboarding-report.json), existing UI code, product copy, route names, component names, and any existing `docs/*` project docs to infer architecture and product background.
4. If `repoEvidence.designEvidenceSummary` exists, treat it as the machine-readable snapshot of the current visual system, token bypasses, and UI surface inventory before proposing a new direction.
5. When analyzing an existing UI codebase, inspect low-cost evidence such as hardcoded color density, prop-drilling candidates, breakpoint chaos, CSS variable patterns, and component surface inventory before declaring the current design direction healthy.
6. If [docs/DESIGN.md](../../docs/DESIGN.md) or `docs/design-intent.json` already exists, check for drift and improve them instead of rewriting blindly.
7. If context is incomplete, write explicit assumptions and reversible design bets instead of defaulting to generic SaaS output.
8. Explore multiple plausible design directions internally, then commit to one cohesive direction with clear rationale tied to the product context and at least one memorable signature move.
9. Treat any example structure or stylistic inspiration as non-normative. Use it only to judge depth and clarity, never to copy a visual language directly.
10. All references to docs or rules must be clickable markdown links.
11. Responsive work must adapt layout, navigation, density, and task order across viewports. Shrinking desktop layouts is not enough.
12. Motion can be bold, cinematic, or highly expressive when it improves memorability, hierarchy, feedback, or perceived product quality. Do not flatten everything into static screens. Optimize motion first, and only reject it when it harms clarity, accessibility, or runtime performance.
13. Define how core components morph across interaction states and viewports. Component quality is not only visual styling; it includes behavior under hover, focus, active, loading, error, and constrained layouts.
14. Do not reuse a color palette, component skin, or motion signature from prior chats, memories, or unrelated projects unless current repo evidence or the active brand brief explicitly asks for that continuity.
15. Treat prior website memory, old portfolio styles, and remembered screenshots as tainted context unless the user explicitly asks to continue or evolve that specific visual system.
16. Do not default to balanced card grids, soft startup gradients, safe centered heroes, or neutral dashboard chrome unless the product context explicitly justifies them.

Required `docs/DESIGN.md` sections:
1. Design Intent and Product Personality
2. Audience and Use-Context Signals
3. Visual Direction and Distinctive Moves
4. Color Science and Semantic Roles
5. Typographic Engineering and Hierarchy
6. Spacing, Layout Rhythm, and Density Strategy
7. Token Architecture and Alias Strategy
8. Responsive Strategy and Cross-Viewport Adaptation Matrix
9. Interaction, Motion, and Feedback Rules
10. Component Language, Morphology, and Shared Patterns
11. Accessibility Non-Negotiables
12. Anti-Patterns to Avoid
13. Implementation Notes for Future UI Tasks

Required `docs/design-intent.json` fields:
- `mode`
- `status`
- `project`
- `designPhilosophy`
- `brandAdjectives`
- `antiAdjectives`
- `visualDirection`
- `mathSystems`
- `tokenSystem`
- `colorTruth`
- `crossViewportAdaptation`
- `motionSystem`
- `componentMorphology`
- `experiencePrinciples`
- `forbiddenPatterns`
- `validationHints`
- `requiredDesignSections`
- `implementation`
- `repoEvidence` when onboarding or detector evidence exists

Output:
- Create or update both `docs/DESIGN.md` and `docs/design-intent.json`.
- Keep both files synchronized: the markdown explains the why, the JSON captures the contract in machine-readable form.
- `docs/design-intent.json` must define a real token system, not just loose style notes. Include primitive, semantic, and component layers plus aliasing rules and naming constraints.
- `docs/design-intent.json` must include deterministic fields for `colorTruth.format`, `colorTruth.allowHexDerivatives`, and `crossViewportAdaptation.mutationRules.mobile/tablet/desktop`.
- `docs/design-intent.json` must also include `motionSystem` and `componentMorphology` so future UI work preserves state behavior and purposeful motion without collapsing into generic static output.
- If onboarding or detector evidence exists, preserve it under `repoEvidence.designEvidenceSummary` instead of throwing away the machine-readable snapshot of the current UI system.
- Token intent must stay structure-first: primitive tokens hold raw values, semantic tokens carry purpose, and component tokens consume semantic tokens instead of bypassing them with raw values.
- Color intent must be defined in a perceptual or relational color model first. Hex values may appear only as implementation derivatives.
- The contract must encode viewport mutation rules, not just breakpoint names.
- Motion guidance must preserve creativity: allow meaningful animation, define reduced-motion behavior, and optimize choreography instead of suppressing it by default.
- Color direction must come from the current project context. Similarity to prior unrelated projects is drift unless the brief or repo evidence explicitly supports it.
- If no approved reference system exists, synthesize the design from zero using current product context, constraints, and content only.
- The resulting system should feel authored and recognizable in screenshots, not politely interchangeable with common template kits.
- Use practical, modern, accessible language grounded in the project, not generic SaaS defaults or copycat brand systems.
- Wait for user approval before generating Figma or code assets.
