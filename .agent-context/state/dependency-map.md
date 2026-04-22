# Dependency Map (State Awareness)

> This map documents allowed dependency direction to prevent circular references during refactors.

## Layer Dependency Rules

1. Transport layer may depend on Service layer.
2. Service layer may depend on Domain contracts and Repository interfaces.
3. Infrastructure layer may implement Repository interfaces.
4. Domain layer must not depend on Transport or Infrastructure.

## Module-Level Constraints

| Source Module | Allowed Dependencies | Forbidden Dependencies |
|---------------|----------------------|------------------------|
| `authentication` | `shared`, `user` | `payment` internals |
| `payment` | `shared`, `billing`, `notification` contracts | `authentication` internals |
| `reporting` | `shared`, read-only repository ports | write-side service internals |
| `frontend` | public API clients only | direct repository access |

## Circular Dependency Guardrail

When refactoring:

1. Detect import graph changes before applying bulk edits.
2. Reject any change introducing `A -> B -> A` cycles.
3. Move shared contracts to `shared` module when two-way dependencies appear.

## Project-Specific Notes

- Replace sample modules with your real domain modules.
- Keep this map synchronized with architecture decisions and ADRs.
