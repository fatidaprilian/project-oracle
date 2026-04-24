
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
17. For design work, only these count as valid style context by default: current repo evidence, the current user brief, current project docs, and explicitly approved reference systems.
18. Design continuity is opt-in. If the user does not explicitly ask for continuity with an older system, prefer fresh synthesis from the current repo and brief.
19. Accessibility must be split into a hard compliance floor and an advisory readability layer. Use WCAG 2.2 AA as the blocking baseline, and use APCA only as advisory perceptual tuning. APCA must never waive a WCAG failure.
20. Accessibility planning must cover more than color contrast. It must explicitly address focus visibility, focus appearance, target size, keyboard access, accessible authentication, and dynamic state/status access.
21. Structured design execution must stay representation-first. Define a surface plan, component graph, content-priority map, viewport mutation plan, and interaction-state matrix before relying on semantic review.
22. Do not depend on screenshot capture, browser automation, or image diff artifacts as the default path. The contract must be strong enough to guide precise UI from repo evidence, component logic, and user intent alone.
23. Semantic review should judge contract fidelity, distinctiveness, hierarchy, state behavior, and viewport mutation directly from the contract and changed UI code.
24. Distinctive design review must use a stable review rubric. The contract should define how to judge distinctiveness, contract fidelity, visual consistency, heuristic UX quality, and motion discipline without collapsing those into one vague taste score.
25. Genericity findings must name the actual drift signal. Do not say "generic" without tying it to a rubric dimension or explicit anti-pattern.
26. Separate taste from failure. A bold design is valid when it still follows the contract, serves the product, and respects accessibility and runtime constraints.

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
11. Context Hygiene and Approved Reference Boundaries
12. Accessibility Non-Negotiables
13. Anti-Patterns to Avoid
14. Implementation Notes for Future UI Tasks

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
- `accessibilityPolicy`
- `designExecutionPolicy`
- `designExecutionHandoff`
- `reviewRubric`
- `contextHygiene`
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
- `docs/design-intent.json` must also include `accessibilityPolicy` so the hard compliance floor, advisory contrast model, and blocking-vs-advisory checks stay machine-readable.
- `docs/design-intent.json` must also include `designExecutionPolicy` so structured handoff rules, representation strategy, semantic review focus, and non-screenshot execution boundaries stay machine-readable.
- `docs/design-intent.json` must also include `designExecutionHandoff` so surface plans, component graph relationships, content priority, viewport mutation, interaction states, and signature move rationale are explicit before implementation begins.
- `docs/design-intent.json` must also include `reviewRubric` so distinctiveness, genericity drift, taste-vs-failure boundaries, and motion discipline are judged with stable dimensions instead of ad hoc opinion.
- `docs/design-intent.json` must include `contextHygiene` so valid design sources, tainted carryover sources, and continuity rules are machine-readable.
- If onboarding or detector evidence exists, preserve it under `repoEvidence.designEvidenceSummary` instead of throwing away the machine-readable snapshot of the current UI system.
- Token intent must stay structure-first: primitive tokens hold raw values, semantic tokens carry purpose, and component tokens consume semantic tokens instead of bypassing them with raw values.
- Color intent must be defined in a perceptual or relational color model first. Hex values may appear only as implementation derivatives.
- The contract must encode viewport mutation rules, not just breakpoint names.
- Motion guidance must preserve creativity: allow meaningful animation, define reduced-motion behavior, and optimize choreography instead of suppressing it by default.
- Accessibility guidance must split hard compliance from advisory tuning: treat WCAG 2.2 AA as the minimum blocking floor and APCA as advisory perceptual guidance for readability nuance, especially in typography and dark mode.
- Accessibility scope must include focus visibility, focus appearance, target size, accessible authentication, keyboard access, use-of-color-only failures, and dynamic status/state access.
- Structured design execution guidance must define the surface plan, component graph, content-priority map, viewport mutation plan, interaction-state matrix, and semantic review focus without relying on screenshot capture.
- Structured design execution must include an explicit structured handoff in `docs/design-intent.json`, not just policy booleans. The handoff should be detailed enough that a future agent can implement the UI without falling back to generic layout defaults.
- The review rubric must define stable dimensions, genericity signals, valid bold signals, and reporting rules that force the agent to explain why something is generic or valid.
- Color direction must come from the current project context. Similarity to prior unrelated projects is drift unless the brief or repo evidence explicitly supports it.
- If no approved reference system exists, synthesize the design from zero using current product context, constraints, and content only.
- Explicitly record which sources are allowed to shape the visual language and which sources are tainted unless the user opts into continuity.
- The resulting system should feel authored and recognizable in implementation, not politely interchangeable with common template kits.
- Use practical, modern, accessible language grounded in the project, not generic SaaS defaults or copycat brand systems.
- Wait for user approval before generating Figma or code assets.
