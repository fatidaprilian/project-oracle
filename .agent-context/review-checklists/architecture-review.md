# Architecture Review Checklist

> Run this when reviewing module structure, new feature design, or refactoring.
> Bad architecture is invisible until it becomes unmaintainable.

## Instructions for Agent

Evaluate every item against the current project structure. For each violation, explain:
1. What layer or boundary is broken
2. Why it leads to maintenance or scalability problems
3. The correct architectural pattern to apply

---

## Layer Separation

- [ ] **Controllers/Handlers contain NO business logic** — Only parsing input, calling service, formatting response
- [ ] **Services contain NO HTTP concepts** — No `Request`, `Response`, `HttpStatus` imports
- [ ] **Services contain NO raw SQL or direct DB access** — Use repository/DAO layer
- [ ] **Repositories contain NO business rules** — Only CRUD and query operations
- [ ] **Domain entities have NO framework dependencies** — Pure language types only
- [ ] **Dependencies flow inward** — Transport → Service → Repository → Domain (never reverse)

## Module Boundaries

- [ ] **Modules don't import from each other's internal files** — Only public exports
- [ ] **No circular dependencies between modules** — A → B → A is forbidden
- [ ] **Each module has a clear single responsibility** — Not a "kitchen sink" module
- [ ] **Shared code is genuinely shared** — Not domain-specific code disguised as "common"
- [ ] **Module size is reasonable** — If a module has 20+ files, consider splitting

## Backend Universal Principles

- [ ] **No clever hacks in backend and shared core modules** — Prefer explicit flow over language tricks that hide intent
- [ ] **No premature abstraction** — Introduce shared abstractions only after repeated, stable patterns emerge
- [ ] **Readability over brevity** — Prefer clear multi-line logic over compressed one-liners

## Dependency Management

- [ ] **No God classes** — No class/file with 500+ lines or 10+ dependencies
- [ ] **Constructor injection only** — No service locator, no field injection, no global state
- [ ] **Interfaces defined where consumed** — Not in the implementation module
- [ ] **External services abstracted behind interfaces** — Swappable, testable
- [ ] **Configuration injected, not hardcoded** — No magic strings for URLs, ports, keys

## Data Flow

- [ ] **DTOs at boundaries** — Internal models don't leak to external interfaces
- [ ] **Validation at entry points** — Zod / Pydantic / Bean Validation at transport layer
- [ ] **No raw request objects passed deep** — Transform to domain types ASAP
- [ ] **Response transformation explicit** — Dedicated serializers / resources / mappers
- [ ] **Sensitive data excluded from responses** — Passwords, tokens, internal IDs

## Database Design

- [ ] **Migrations are incremental** — No destructive changes without migration plan
- [ ] **Foreign keys for data integrity** — Relations enforced at DB level
- [ ] **Indexes for query patterns** — Not just primary keys
- [ ] **No business logic in DB** — Triggers and stored procs used sparingly
- [ ] **Soft delete considered** — For audit-sensitive entities

## Error Architecture

- [ ] **Error hierarchy defined** — Base error class with domain-specific subtypes
- [ ] **Global error handler exists** — Catches unhandled errors, returns safe responses
- [ ] **Error codes are typed** — Enum or const, not arbitrary strings
- [ ] **Client errors vs server errors distinguished** — 4xx vs 5xx with different handling
- [ ] **Errors don't leak internals** — No stack traces, SQL errors, or file paths to client

## Scalability Readiness

- [ ] **Stateless services** — No in-memory session or request state across requests
- [ ] **Background jobs for heavy work** — Long operations don't block HTTP responses
- [ ] **Idempotent endpoints where needed** — POST with idempotency keys for payment/creation
- [ ] **Feature flags for gradual rollout** — New features can be toggled without deploy
- [ ] **Health check endpoint exists** — `/health` returning service status
