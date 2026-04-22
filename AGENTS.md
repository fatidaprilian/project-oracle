# AGENTS.md - Thin Adapter

Adapter Mode: thin
Adapter Source: .instructions.md
Canonical Snapshot SHA256: 060b739f87a77375f261a13c3b2b295993ba67b4172420c4223ba1332d47b0a3

This file is an adapter entrypoint for agent discovery.
The canonical policy source is [.instructions.md](.instructions.md).

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
