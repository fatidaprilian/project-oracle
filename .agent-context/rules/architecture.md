# Architecture — Separation of Concerns & Structure

> If your service file imports an HTTP library, your architecture is broken.
> If your controller contains SQL, you've already lost.

## Universal Backend Principles (Mandatory)

These principles are mandatory for backend and shared core modules.

- No clever hacks. Prefer explicit control flow over language tricks that hide intent.
- No premature abstraction. Extract shared utilities or base types only after repeated, stable patterns appear.
- Readability over brevity. Reject compressed one-liners when clearer multi-line logic is easier to review.

If a short and a clear implementation are functionally equivalent, choose the clear implementation.

## Universal SOP Baseline (Mandatory)

The `.agent-context/rules/` directory is the default guidance source for implementation and review.

- Backend and frontend mindset checks are both required when a task spans API and UI boundaries.
- Security and testing are non-negotiable baseline requirements.
- Hard block before coding:
  - `docs/project-brief.md` must exist.
  - `docs/architecture-decision-record.md` (alias: `docs/Architecture-Decision-Record.md`) must exist.
  - `docs/flow-overview.md` must exist.
  - If the project uses persistent data, `docs/database-schema.md` must exist.
  - If the project exposes API or web application flows, `docs/api-contract.md` must exist.
  - For UI scope, `docs/DESIGN.md` and `docs/design-intent.json` must exist.
- If required project context docs are missing, stop implementation and bootstrap docs before writing application code.
- Bootstrap flow: analyze the real repo plus the latest user prompt before authoring those docs.
- Bootstrap docs must be adaptive and project-specific. Do not create generic placeholder templates.
- When context is incomplete, separate confirmed facts from assumptions, add an `Assumptions to Validate` section, and end with the next validation action.

## Rules as Guardian (Cross-Session Consistency)

These guardrails are mandatory to preserve architecture direction across sessions.

- Session handoff must include active architecture contract summary.
- Contract summary must include declared stack, blueprint, profile, and active core patterns.
- Detect drift before changing declared stack or core patterns.
- Direction changes require explicit user confirmation before applying changes.
- When confirmation is provided, record the rationale in session notes or PR context.

## Invisible State Management with Explain-on-Demand

State internals must stay invisible by default.

- Default responses must avoid unnecessary state-file internals.
- State internals are exposed only on explicit user request.
- Diagnostic mode explains relevant state decisions when needed.
- Keep default explanations concise and outcome-first; show raw state details only in diagnostic mode.

## Single Source of Truth and Lazy Rule Loading

- Canonical rule source is .instructions.md.
- Adapter entry files stay thin and must point to the canonical source.
- Load language-specific stack guidance lazily based on detected scope.
- Do not preload unrelated stack profiles during normal flow.
- Keep rule-loading output deterministic for init and release validation.

## The Core Principle

**Every layer has ONE job. Layer leaks are bugs — not "pragmatic shortcuts."**

```
┌─────────────────────────────────────────┐
│         TRANSPORT / CONTROLLER          │  ← Parse input, validate shape, return response
│         (HTTP, CLI, WebSocket, Queue)   │  ← NO business logic here. EVER.
├─────────────────────────────────────────┤
│         APPLICATION / SERVICE           │  ← Business rules, orchestration, transactions
│         (Use cases, workflows)          │  ← NO HTTP, NO SQL, NO framework imports
├─────────────────────────────────────────┤
│         DOMAIN / ENTITY                 │  ← Pure business objects, value objects
│         (Models, rules, calculations)   │  ← ZERO external dependencies
├─────────────────────────────────────────┤
│         INFRASTRUCTURE / REPOSITORY     │  ← Database, external APIs, file system
│         (Data access, adapters)         │  ← NO business logic
└─────────────────────────────────────────┘
```

## Layer Rules (Enforced)

### Transport Layer (Controller / Handler / Route)
**Allowed:**
- Parse and validate incoming request (DTO/schema validation)
- Call application/service layer
- Format and return HTTP response (status code, headers)
- Handle authentication/authorization middleware

**BANNED:**
- Database queries or ORM calls
- Business logic (if/else on business rules)
- Direct calls to external APIs
- Transaction management

### Application Layer (Service / Use Case)
**Allowed:**
- Orchestrate business operations
- Call repository layer for data
- Apply business rules and validations
- Manage transactions
- Emit domain events

**BANNED:**
- HTTP request/response objects
- Framework-specific decorators (keep framework coupling minimal)
- Direct SQL or raw database calls
- UI/presentation logic

### Domain Layer (Entity / Value Object)
**Allowed:**
- Business calculations and rules
- Validation of domain invariants
- Type definitions and interfaces

**BANNED:**
- ANY external dependency (database, HTTP, framework)
- Side effects (logging, API calls, file I/O)
- Infrastructure concerns

### Infrastructure Layer (Repository / Adapter)
**Allowed:**
- Database queries (SQL, ORM, document queries)
- External API calls (wrapped in adapters)
- File system operations
- Cache operations

**BANNED:**
- Business logic (no if/else on business rules in queries)
- HTTP response formatting
- Direct exposure to transport layer

---

## Dependency Direction

Dependencies flow **inward only**:

```
Transport → Application → Domain ← Infrastructure
                ↓
          Infrastructure

NEVER: Domain → Infrastructure (use interfaces/ports)
NEVER: Application → Transport
NEVER: Infrastructure → Application (except through interfaces)
```

The Domain layer depends on NOTHING. Everything depends on the Domain.

---

## Default Architecture: Modular Monolith

Start with a **Modular Monolith**. Do NOT start with microservices.

**Switch to microservices ONLY if 2+ of these triggers exist:**
1. Frequent deploy conflicts across domains (teams blocking each other)
2. Clear scale mismatch (one module needs 100x resources of another)
3. Team ownership collision (multiple teams editing same module)
4. Fault isolation requirement (one module crashing must not kill others)
5. Stable contracts with clear data boundaries already exist

If these triggers don't exist, microservices are **premature complexity**.

---

## Project Structure: Feature-Based Grouping

## Code Organization and File Size Discipline

Keep modules small enough to understand in one focused read.

- Prefer grouping by responsibility, not by convenience.
- One folder should represent one clear area of responsibility.
- Split discovery, validation, prompt building, persistence, and contract logic into separate modules when they grow.
- Avoid mixed-purpose mega-files that combine constants, parsing, orchestration, validation, and I/O in one place.
- Treat files above roughly 1000 lines as a refactor trigger, not a badge of completeness.
- If a file grows past that threshold, extract stable submodules with clear names before adding more behavior.
- Preserve one public entrypoint when it helps callers, but move the real implementation behind focused modules.
- Tests may aggregate scenarios, but shared helpers and repeated setup should move into dedicated support files when the suite becomes hard to scan.

### ❌ BANNED: Technical Grouping
```
src/
  controllers/          ← 50 controllers in one flat folder?
    userController.ts
    orderController.ts
    paymentController.ts
  services/             ← Good luck finding related code
    userService.ts
    orderService.ts
  repositories/
    userRepository.ts
    orderRepository.ts
```

### ✅ REQUIRED: Feature/Domain Grouping
```
src/
  modules/                              ← Backend
    user/
      user.controller.ts               ← Transport
      user.service.ts                   ← Application
      user.repository.ts               ← Infrastructure
      user.entity.ts                    ← Domain
      user.dto.ts                       ← Data Transfer Objects
      user.module.ts                    ← Module registration
      __tests__/
        user.service.test.ts
    order/
      order.controller.ts
      order.service.ts
      ...
  shared/                               ← Cross-cutting concerns
    config/
    errors/
    logging/
    middleware/

src/
  features/                             ← Frontend
    payment/
      api/                              ← HTTP client + DTOs
      hooks/                            ← React hooks / state
      components/                       ← UI components
      types/                            ← Type definitions
      utils/                            ← Feature-specific utils
      index.ts                          ← Public API barrel
  components/
    ui/                                 ← Shared UI primitives
    layout/                             ← Layout components
  lib/                                  ← Shared utilities
  config/                               ← App configuration
```

---

## Module Communication

### Within a Monolith
Modules communicate through **public interfaces only**:
```
// ✅ CORRECT: Import from module's public API
import { UserService } from '@/modules/user';

// ❌ BANNED: Reach into another module's internals
import { UserRepository } from '@/modules/user/user.repository';
```

### Between Services (if microservices)
- Use well-defined contracts (REST, gRPC, events)
- Never share databases between services
- Define schemas at boundaries (Protobuf, JSON Schema, Zod)

---

## The Architecture Smell Test

Ask yourself these questions. If ANY answer is "yes", your architecture is broken:

1. Can I change the database without touching business logic? (Must be YES)
2. Can I switch from REST to GraphQL without rewriting services? (Must be YES)
3. Can I test business logic without a running database? (Must be YES)
4. Does each module have a clear, single responsibility? (Must be YES)
5. Can a new developer find all related code in one directory? (Must be YES)
