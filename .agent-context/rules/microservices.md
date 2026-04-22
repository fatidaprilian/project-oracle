# Microservices — When to Split, How to Split

> Don't start with microservices. Earn them through pain.
> A bad monolith becomes a distributed bad monolith faster than you think.

## The Default: Modular Monolith

**Start with a modular monolith. Always.** Microservices are a scaling strategy, not a design philosophy.

A well-structured modular monolith can handle most applications indefinitely. Splitting prematurely creates distributed complexity without distributed benefits.

---

## The Split Decision Framework

### Prerequisites (ALL Must Be True)

Before even considering microservices, these must exist:

1. **Mature CI/CD pipeline** — automated testing, deployment, rollback
2. **Observability in place** — distributed tracing, centralized logging, metrics
3. **Team maturity** — team understands distributed systems failure modes
4. **Clear module boundaries** — modules already communicate through interfaces, not internals

If any prerequisite is missing, **stop.** Fix the monolith first.

### Trigger Conditions (2+ Required)

Split a module into a service ONLY when **2 or more** of these triggers exist:

| # | Trigger | Evidence |
|---|---------|----------|
| 1 | **Deploy conflicts** | Teams block each other on releases; merge queues exceed 24h |
| 2 | **Scale mismatch** | One module needs 50-100x resources of another |
| 3 | **Team ownership collision** | Multiple teams edit the same module weekly |
| 4 | **Fault isolation** | One module crashing must not kill the entire system |
| 5 | **Technology divergence** | Module genuinely requires a different runtime/language |
| 6 | **Compliance boundary** | Regulatory requirement to isolate data processing (PCI, HIPAA) |

```
BANNED: "Let's use microservices because Netflix does"
BANNED: "We might need to scale later"
BANNED: "It's more modern"
BANNED: "Each developer gets their own service"
```

---

## How to Split (The Extraction Protocol)

### Step 1: Identify the Seam

Find the natural boundary in your modular monolith:
```
GOOD seams:
  - Module communicates with others through a defined interface/API
  - Module has its own database tables with no foreign keys to other modules
  - Module can be deployed independently without breaking others

BAD seams:
  - Two modules share a database table
  - Extracting requires duplicating business logic
  - Module makes 10+ synchronous calls to other modules per request
```

### Step 2: Strangle, Don't Rewrite

```
❌ BANNED: "Let's rewrite everything as microservices"

✅ REQUIRED: The Strangler Fig Pattern
1. Build the new service alongside the monolith
2. Route traffic to the new service gradually (feature flags, proxy rules)
3. Verify the new service handles all cases correctly
4. Remove the old code from the monolith
5. Repeat for the next service, ONE AT A TIME
```

### Step 3: Define the Contract

Before extracting, define the communication contract:

```
REQUIRED for every service boundary:
- API contract (OpenAPI 3.1, Protobuf, or AsyncAPI for events)
- Versioning strategy (URL versioning, header versioning)
- Error contract (standardized error response format)
- SLA definition (latency, availability, throughput)
- Ownership (which team owns this service)
```

---

## Communication Patterns

### Synchronous (Request-Response)

| Pattern | When | Watch Out |
|---------|------|-----------|
| REST/HTTP | Standard CRUD operations | Cascading failures, tight coupling |
| gRPC | High-performance, internal services | Schema evolution, debugging complexity |

**Rules:**
- Always set timeouts (connection: 1s, request: 5s default)
- Implement circuit breakers (fail-fast after N failures)
- Never chain more than 3 synchronous calls
- Implement retries with exponential backoff (transient errors only)

### Asynchronous (Events)

| Pattern | When | Watch Out |
|---------|------|-----------|
| Pub/Sub | One event, multiple consumers | Message ordering, at-least-once delivery |
| Command Queue | Exactly-once processing needed | Dead letter queues, poison messages |
| Event Sourcing | Full audit trail required | Complexity, event schema evolution |

**Rules:**
- Prefer async communication over sync between services
- Events are facts (past tense): `OrderPlaced`, `PaymentProcessed`
- Commands are requests (imperative): `ProcessPayment`, `ShipOrder`
- Always handle duplicate messages (idempotency)

---

## Data Ownership

### The Database-Per-Service Rule

```
❌ DEATH PENALTY: Shared databases between services
   Service A → Database ← Service B
   // One schema change breaks both services

✅ REQUIRED: Each service owns its data
   Service A → Database A
   Service B → Database B
   // Services communicate through APIs or events
```

### Data Consistency

- **Accept eventual consistency** — strong consistency across services is extremely expensive
- **Use the Saga pattern** for distributed transactions (choreography or orchestration)
- **Never use distributed 2PC (two-phase commit)** in production — it doesn't scale

---

## Anti-Patterns (Instant Rejection)

| Anti-Pattern | Why It's Dangerous |
|-------------|-------------------|
| **Distributed Monolith** | Services that must be deployed together defeat the purpose |
| **Nano-services** | One function per service creates operational nightmare |
| **Shared libraries with logic** | Tight coupling through shared code |
| **Synchronous chains** | A→B→C→D means one failure kills everything |
| **Shared database** | Schema changes break multiple services |
| **"We'll figure out observability later"** | You won't find bugs without tracing. Ever. |

---

## The Microservices Readiness Checklist

Before splitting ANY module:

- [ ] 2+ trigger conditions met (documented with evidence)
- [ ] All prerequisites in place (CI/CD, observability, team maturity)
- [ ] Service boundary defined with clear ownership
- [ ] API contract defined (OpenAPI, Protobuf, AsyncAPI)
- [ ] Data ownership clear — no shared tables
- [ ] Communication pattern chosen (sync vs async)
- [ ] Failure handling designed (timeouts, circuit breakers, retries)
- [ ] Monitoring and alerting planned
- [ ] Rollback strategy defined
- [ ] Team agrees this is the right decision (not just the architect)
