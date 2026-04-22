# Prompt: Refactor Code

> Copy-paste this prompt when code needs restructuring to follow the rules.

---

## The Prompt

```
Refactor the following code (or module) to comply with our engineering standards.

Before making changes:
1. Read .agent-context/rules/architecture.md — ensure proper layer separation.
2. Read .agent-context/rules/naming-conv.md — fix all naming violations.
3. Read .agent-context/rules/error-handling.md — fix error handling patterns.
4. Resolve active language guidance from dynamic stack signals (TypeScript in this repository).
5. Enforce backend universal principles: no clever hacks, no premature abstraction, readability over brevity.
6. Enforce Universal SOP hard gate: stop implementation if `docs/architecture-decision-record.md` is missing, and for UI scope stop if `docs/DESIGN.md` or `docs/design-intent.json` is missing.

For every change you make, provide a Reasoning Chain:
- What was wrong (rule reference)
- Why it was wrong (explain the risk/problem)
- What you changed (show the improvement)

Refactor guidance:
- Prioritize maintainability over compressed one-liners.
- Prefer explicit readable control flow when short forms hide intent.
- Do not introduce shared abstractions before patterns are repeated and stable.

Maintain ALL existing functionality. This is a refactor, not a rewrite.
Add or update tests if the refactored code changes behavior contracts.
```

## Extract Module Prompt

```
Extract [FEATURE_NAME] into its own module following .agent-context/rules/architecture.md:

1. Create the module directory: src/modules/[feature-name]/
2. Separate into layers:
   - controller (transport — HTTP in/out only)
   - service (business logic — no HTTP, no SQL)
   - repository (data access — no business rules)
   - dto (Zod schemas for input validation)
   - types (type definitions)
3. Create barrel export (index.ts) exposing ONLY the public API
4. Update imports in consuming modules to use the new module path
5. Add unit tests for the service layer

Follow naming-conv.md for all file and variable names.
Provide a Reasoning Chain for every structural decision.
```
