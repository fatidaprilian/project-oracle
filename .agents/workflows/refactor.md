---
description: Refactor code or extract a module following architecture and naming rules
---

## Workflow: Refactor Code

1. Read `.agent-context/rules/architecture.md` to understand the required layer separation.

2. Read `.agent-context/rules/naming-conv.md` to understand naming standards.

3. Read `.agent-context/rules/error-handling.md` to understand error handling patterns.

4. Resolve the active language profile from dynamic stack signals (e.g., TypeScript guidance).

5. Analyze the target code for violations:
   - Layer leaks (business logic in controllers, SQL in services)
   - Naming violations (generic names, missing verb prefixes, missing boolean prefixes)
   - Error handling issues (swallowed errors, generic Error types)
   - Type safety issues (any types, unvalidated input)

6. Apply refactoring while maintaining ALL existing functionality:
   - Separate into proper layers if needed (controller/service/repository)
   - Fix all naming violations
   - Add Zod validation at boundaries if missing
   - Replace generic errors with typed error classes

7. For every change, provide a Reasoning Chain explaining what was wrong and why the new approach is better.

8. Run `.agent-context/review-checklists/pr-checklist.md` as a final quality gate.
