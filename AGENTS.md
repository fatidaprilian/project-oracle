# AGENTS.md - Thin Adapter

Adapter Mode: thin
Adapter Source: .instructions.md
Canonical Snapshot SHA256: 3ddc44d1c3cad20aa06e31c45b5d7289b1b4cde46decb668b0347817222fb022

This file is an adapter entrypoint for agent discovery.
The canonical policy source is [.instructions.md](.instructions.md).

If your host stops at this file instead of following the full chain, obey the Critical Bootstrap Floor below before coding.

## Critical Bootstrap Floor

- If `.agent-instructions.md` exists, prefer it immediately after this file because it is the compiled project-specific snapshot.
- Memory continuity does not replace bootstrap loading. It is host-dependent project memory, not a guarantee that instructions were reloaded for this session.
- For UI, UX, layout, screen, tailwind, frontend, or redesign requests: load [.agent-context/prompts/bootstrap-design.md](.agent-context/prompts/bootstrap-design.md) and [.agent-context/rules/frontend-architecture.md](.agent-context/rules/frontend-architecture.md) before editing code.
- For UI scope: if `docs/DESIGN.md` or `docs/design-intent.json` is missing, materialize or refine them before implementing UI changes.
- For refactor, improve, clean up, or fix requests: inspect the active rules and propose a plan before editing.
- For new project or module requests: propose architecture before generating code.
- For ecosystem, framework, dependency, or Docker claims: perform live web research instead of relying on stale local heuristics.

## Mandatory Bootstrap Chain

1. Load [.instructions.md](.instructions.md) first as the canonical baseline.
2. If `.agent-instructions.md` exists, read it next as the compiled project-specific snapshot.
3. Read baseline governance from [.agent-context/rules/](.agent-context/rules).
4. Apply request templates from [.agent-context/prompts/](.agent-context/prompts).
5. Enforce review contracts from [.agent-context/review-checklists/](.agent-context/review-checklists).
6. Read change-risk maps and continuity state from [.agent-context/state/](.agent-context/state).
7. Enforce policy thresholds from [.agent-context/policies/](.agent-context/policies).
8. Use dynamic stack and architecture reasoning from project context docs and live research signals.

## Trigger Rules

- New project or module requests: propose architecture first and wait for approval.
- Refactor or fix requests: propose plan first, then execute safely.
- Completion: run [.agent-context/review-checklists/pr-checklist.md](.agent-context/review-checklists/pr-checklist.md) before declaring done.

If this adapter drifts from canonical behavior, refresh from [.instructions.md](.instructions.md) and update the hash metadata.
