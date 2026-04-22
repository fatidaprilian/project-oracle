# PR Checklist — The Quality Gate

> Run this before declaring any task "done."
> If ANY item fails, the task is NOT complete.

## Instructions for Agent

When asked to review code using this checklist, evaluate EVERY item below.
For each failed item, provide a Reasoning Chain (see `.cursorrules` → Reasoning Clause).
Output format:

```
## PR REVIEW RESULTS
━━━━━━━━━━━━━━━━━━━

PASS [Item]
FAIL [Item]
   Rule: [rule file + section]
   Problem: [specific issue found]
   Fix: [what to change]

VERDICT: PASS / FAIL (X/Y items passed)
```

---

## The Checklist

### 1. Naming (→ rules/naming-conv.md)
- [ ] All variables are descriptive nouns (no `data`, `temp`, `val`, `x`)
- [ ] All functions start with a verb (no `userData()`, `orderLogic()`)
- [ ] All booleans use `is/has/can/should` prefix
- [ ] Constants use SCREAMING_SNAKE_CASE with unit suffix
- [ ] No single-letter variables (except `i` in classic for-loops)
- [ ] File names follow the project's chosen convention consistently

### 2. Architecture (→ rules/architecture.md)
- [ ] No layer leaks (controllers don't query DB, services don't return HTTP responses)
- [ ] Feature-based file organization (not technical grouping)
- [ ] Dependencies flow inward (transport → service → repository)
- [ ] Module boundaries respected (no reaching into another module's internals)
- [ ] Domain layer has zero external dependencies
- [ ] No clever hacks in backend and shared core modules (prefer explicit control flow)
- [ ] No premature abstraction (base classes/util layers created only after repeated stable patterns)
- [ ] Readability over brevity for maintainability (no compressed one-liners that hide intent)

### 3. Type Safety (→ dynamic TypeScript stack guidance)
- [ ] No `any` type anywhere (use `unknown` + narrowing)
- [ ] No `// @ts-ignore` (use `@ts-expect-error` with justification comment)
- [ ] All function return types are explicit
- [ ] Zod schemas validate ALL external input at boundaries
- [ ] Types derived from Zod schemas (single source of truth)

### 4. Error Handling (→ rules/error-handling.md)
- [ ] No empty catch blocks
- [ ] No `catch(e) { console.log(e) }` without re-throw or recovery
- [ ] Typed error classes used (not generic `new Error('...')`)
- [ ] Error responses don't leak internal details to clients
- [ ] Structured logging with context (traceId, userId, action)

### 5. Security (→ rules/security.md)
- [ ] All user input validated at boundaries (Zod/schema)
- [ ] No SQL/command string concatenation with user input
- [ ] No secrets hardcoded in source code
- [ ] Auth checked server-side (not client-side only)
- [ ] Error messages don't reveal internal system details
- [ ] CORS configured (not `*` in production)

### 6. Performance (→ rules/performance.md)
- [ ] No N+1 queries (no queries inside loops)
- [ ] All list queries have LIMIT/pagination
- [ ] No `SELECT *` (only needed columns)
- [ ] No synchronous I/O in async context
- [ ] Cache has documented invalidation strategy (if caching used)

### 7. Testing (→ rules/testing.md)
- [ ] Business logic has unit tests
- [ ] Test names follow `should [behavior] when [condition]`
- [ ] Tests follow AAA pattern (Arrange → Act → Assert)
- [ ] No implementation detail testing (test behavior, not structure)
- [ ] Test data uses factories (no copy-pasted objects)

### 8. Dependencies (→ rules/efficiency-vs-hype.md)
- [ ] No new dependencies added without justification
- [ ] No dependency that replaces < 20 lines of code
- [ ] New packages checked for maintenance health
- [ ] Bundle impact considered (frontend)

### 9. Git (→ rules/git-workflow.md)
- [ ] Commit messages follow Conventional Commits
- [ ] No `console.log` debugging statements
- [ ] No `// TODO` without a linked issue
- [ ] No commented-out code blocks
- [ ] `.env` not committed

### 10. Documentation
- [ ] Scope applied: This applies to documentation, release notes, onboarding text, review summaries, and agent-facing explanations
- [ ] Style scope review is advisory and does not block merge when API docs are synced in the same commit and contract details are correct
- [ ] Public surface changes fail review if documentation updates are missing or stale in the same scope
- [ ] API endpoint/contract changes include synchronized API/OpenAPI documentation updates
- [ ] Database structure changes include synchronized schema or migration documentation updates
- [ ] Documentation checks stay boundary-aware and only enforce touched scopes
- [ ] API endpoints have OpenAPI/Swagger documentation
- [ ] Complex business logic has comments explaining WHY
- [ ] Public functions/methods have JSDoc/docstrings
- [ ] README updated if new setup steps required
- [ ] No emoji in formal documentation or review summaries
- [ ] Documentation uses plain English and avoids AI cliches
- [ ] Performance/quality claims include source and timestamp
- [ ] Acronyms are expanded on first use
- [ ] Facts and assumptions are explicitly separated

### 11. Context-Triggered Audit Mode
- [ ] Strict audit mode activates automatically on review and PR-intent workflows
- [ ] Small edits avoid heavy checks by default unless strict mode is explicitly requested
- [ ] User can always force strict audit mode manually

### 12. Rules as Guardian (Cross-Session Consistency)
- [ ] Session handoff includes active architecture contract summary
- [ ] Drift detection warns before direction changes
- [ ] Direction changes require explicit user confirmation

### 13. Invisible State Management (Explain-on-Demand)
- [ ] Default responses avoid unnecessary state-file internals
- [ ] State internals are exposed only on explicit request
- [ ] Diagnostic mode can explain relevant state decisions when needed

### 14. Single Source and Lazy Rule Loading
- [ ] Canonical rule source is explicitly defined and enforced
- [ ] Language-specific guidance is loaded lazily based on detected scope
- [ ] No conflicting duplicate rule instructions during normal flow

### 15. Universal SOP Consolidation
- [ ] `.agent-context/rules/` remains the default guidance source for implementation and review
- [ ] Backend and frontend mindset checks are both applied when scope spans API and UI boundaries
- [ ] Security and testing requirements remain mandatory after static template purge
- [ ] Coding flow is blocked if `docs/architecture-decision-record.md` (or `docs/Architecture-Decision-Record.md`) is missing
- [ ] UI implementation flow is blocked if `docs/DESIGN.md` or `docs/design-intent.json` is missing
