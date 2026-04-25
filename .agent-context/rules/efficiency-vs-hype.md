# Dependency and Tooling Boundary

## Latest-Compatible-First Rule

The LLM may choose modern libraries and tooling when they fit the project. This rule does not prefer "no library" or any fixed dependency set.

Before adding or recommending a dependency:
- check current official docs, release notes, and setup guidance when the ecosystem decision matters
- choose the latest stable compatible dependency version unless a project constraint blocks it
- use the official scaffolder or setup command when it creates the current supported project shape
- Only step down to an older dependency version after documenting the exact compatibility, runtime, platform, or ecosystem reason.
- explain why the dependency improves maintainability, UX, performance, security, or delivery speed
- avoid packages that are stale, thinly maintained, too heavy for the job, or added only because they are popular
- keep dependency boundaries replaceable when the library would spread through many files

Reject offline dependency decisions, outdated tutorial versions, and trend choices that are not grounded in the current repo and brief.
