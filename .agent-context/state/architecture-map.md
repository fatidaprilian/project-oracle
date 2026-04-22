# Architecture Map (State Awareness)

> This file defines protected architectural boundaries for AI-assisted changes.

## Boundary Classification

| Module/Path Pattern | Criticality | Change Policy | Required Checks |
|---------------------|-------------|---------------|-----------------|
| `src/modules/payment/**` | critical | Must preserve transactional behavior and idempotency | Unit + integration + rollback test |
| `src/modules/authentication/**` | critical | Never bypass auth guards or token validation | Security audit + integration tests |
| `src/modules/**/repository/**` | high | Preserve query contracts and avoid N+1 regressions | Query plan review + performance audit |
| `src/features/**` | medium | Keep UI contracts stable and avoid API drift | Component tests + contract checks |
| `src/shared/**` | high | Backward compatibility required for public utilities | Cross-module usage validation |

## Required Agent Behavior

1. Before editing a `critical` area, load `.agent-context/review-checklists/pr-checklist.md` and `.agent-context/review-checklists/architecture-review.md`.
2. For boundary-crossing changes, verify no circular dependencies are introduced (see `dependency-map.md`).
3. Every critical-path change must include explicit risk notes in PR description.

## Project-Specific Notes

- Replace placeholder path patterns with your actual module map.
- Mark payment, identity, and financial reconciliation flows as `critical`.
- Keep this file updated whenever module ownership changes.
