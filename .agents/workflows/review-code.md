description: Run a comprehensive code review using PR and architecture checklists
---

## Workflow: Review Code

1. Read `.agent-context/review-checklists/pr-checklist.md` and apply every item against the current codebase.

2. Read `.agent-context/review-checklists/architecture-review.md` and apply every item against the current codebase.

3. For every violation found, provide a Reasoning Chain:
   - State the exact file and line
   - Reference the specific rule (file + section from `.agent-context/rules/`)
   - Explain WHY it's a problem
   - Provide the corrected code

4. Output results in this format:

```
## PR REVIEW RESULTS
- PASS or FAIL for each item
- Reasoning Chain for each failure

## ARCHITECTURE REVIEW RESULTS
- Boundary violation summary and risk level for each finding
- Specific remediation for each finding

## VERDICT: PASS or FAIL
```
