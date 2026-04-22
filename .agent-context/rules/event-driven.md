# Event-Driven Architecture — React to Facts, Don't Poll for Changes

> If your services are constantly asking "Did anything change?", your architecture is broken.
> Events are the nervous system of a distributed system.

## When to Use Event-Driven Architecture

### Use Events When:
1. Multiple services need to react to the same state change
2. You need temporal decoupling (producer doesn't wait for consumer)
3. Audit trail / event history is a business requirement
4. Systems need to scale producers and consumers independently
5. Eventual consistency is acceptable

### Don't Use Events When:
- You need an immediate, synchronous response
- The system is a simple CRUD application with 1-2 services
- You can't invest in proper infrastructure (message broker, monitoring)
- Your team has no experience with async debugging

---

## Core Patterns

### 1. Pub/Sub (Publish-Subscribe)

Producer emits an event. Zero or more consumers react independently.

```
              ┌──────────┐
              │ Consumer A│ (Send email)
              └────▲──────┘
┌──────────┐      │
│ Producer  │──→ EVENT BUS ──→┌──────────┐
│ (Order    │      │          │ Consumer B│ (Update inventory)
│  Service) │      │          └──────────┘
└──────────┘      │
              ┌───▼──────┐
              │ Consumer C│ (Analytics)
              └──────────┘
```

**Rules:**
- Producer does NOT know about consumers (fire-and-forget)
- Each consumer processes independently (failure in one doesn't affect others)
- Consumers MUST be idempotent (same event processed twice = same result)

### 2. CQRS (Command Query Responsibility Segregation)

Separate the write model (commands) from the read model (queries).

```
┌─────────────┐                  ┌─────────────┐
│ Write Side  │    Events        │  Read Side   │
│ (Commands)  │ ──────────────→  │  (Queries)   │
│             │                  │              │
│ Rich domain │                  │ Denormalized │
│ model       │                  │ read models  │
│ Normalized  │                  │ Optimized    │
│ schema      │                  │ for queries  │
└─────────────┘                  └─────────────┘
```

**When to use CQRS:**
- Read/write ratio is heavily skewed (100:1 reads to writes)
- Read and write models have fundamentally different shapes
- You need different scaling for reads vs writes

**When NOT to use CQRS:**
- Simple CRUD with no complex queries
- Read and write models are identical (just use a repository)
- You don't have the team capacity to maintain two models

### 3. Event Sourcing

Store the full history of state changes as immutable events, not just the current state.

```
Traditional:  User { name: "Jane", email: "jane@new.com" }
              → You only know the current state

Event Sourced:
  1. UserCreated { name: "Jane", email: "jane@old.com" }
  2. EmailChanged { email: "jane@mid.com" }
  3. EmailChanged { email: "jane@new.com" }
  → You know the full history, can rebuild any point in time
```

**When to use Event Sourcing:**
- Audit trail is a regulatory requirement (finance, healthcare)
- "Time travel" queries are needed (what was the state on March 1?)
- Complex domain with many state transitions
- Combined with CQRS for complex read requirements

**When NOT to use Event Sourcing:**
- Simple CRUD applications (overkill)
- Team has no experience with event stores
- No clear business need for historical state

---

## Event Design Rules

### Naming: Past Tense, Domain Language

```
❌ BANNED:
  "UpdateOrder"       → Commands, not events
  "ORDER_UPDATE"      → Screaming snake in an event name
  "data"              → Meaningless

✅ REQUIRED:
  "OrderPlaced"       → Past tense, describes what happened
  "PaymentProcessed"  → Specific, clear domain action
  "InventoryReserved" → Business language, not technical
```

### Event Schema: Include Context

```typescript
// ❌ BANNED: Minimal event with no context
{ type: "OrderPlaced", orderId: "123" }

// ✅ REQUIRED: Rich event with all necessary context
{
  eventId: "evt_abc123",          // Unique, for idempotency
  eventType: "OrderPlaced",       // What happened
  aggregateId: "order_123",       // Which entity
  aggregateType: "Order",         // Entity type
  timestamp: "2026-03-11T...",    // When it happened
  version: 1,                     // Schema version
  correlationId: "req_xyz",       // Trace across services
  causationId: "cmd_456",        // What caused this event
  data: {                         // The event payload
    orderId: "order_123",
    userId: "user_789",
    items: [...],
    totalAmount: 99.99,
    currency: "USD"
  },
  metadata: {                     // Operational metadata
    producerService: "order-service",
    producerVersion: "2.1.0"
  }
}
```

### Event Versioning

Events are immutable — once published, they can't change. Handle evolution with:

1. **Weak schema (preferred):** Consumers ignore unknown fields, use defaults for missing fields
2. **Upcasting:** Transform old events to new schema on read
3. **New event type:** If the change is breaking, create `OrderPlacedV2`

```
BANNED: Changing the schema of an existing event in a breaking way
BANNED: Removing fields from events
ALLOWED: Adding optional fields with defaults
ALLOWED: Creating a new event type for breaking changes
```

---

## Infrastructure Choices

| Need | Recommended | Avoid |
|------|-----------|-------|
| General pub/sub | Apache Kafka, NATS, RabbitMQ | Custom TCP sockets |
| Cloud-native | AWS EventBridge, GCP Pub/Sub, Azure Service Bus | Polling a database table |
| Simple/local | Redis Streams, NATS | ZeroMQ for production events |
| Event store | EventStoreDB, Kafka (with compaction) | Relational DB as event store (unless simple) |

---

## Reliability Patterns

### Outbox Pattern (Transactional Events)

Ensure events are published reliably alongside database writes:

```
1. Write to database AND outbox table in a single transaction
2. Background process reads outbox and publishes to message broker
3. Mark outbox entry as published

This guarantees: if the DB write succeeds, the event WILL be published.
No more "DB updated but event lost" bugs.
```

### Dead Letter Queue (DLQ)

Messages that fail processing after N retries go to a DLQ:
- Monitor DLQ size — it should be near zero
- Alert when DLQ grows
- Investigate and reprocess failed messages
- Never ignore a growing DLQ

### Idempotency (Non-Negotiable)

```
EVERY consumer MUST handle duplicate events safely.

Techniques:
1. Idempotency key: Store processed eventIds, skip if seen
2. Natural idempotency: Operations that are naturally safe to repeat
   (e.g., SET status = 'paid' is idempotent; INCREMENT balance is NOT)
3. Optimistic locking: Use version numbers to detect conflicts
```

---

## The Event-Driven Checklist

Before implementing event-driven patterns:

- [ ] Business justification exists (not just "it's modern")
- [ ] Team understands eventual consistency trade-offs
- [ ] Message broker selected and provisioned
- [ ] Event schema defined with versioning strategy
- [ ] All consumers are idempotent
- [ ] Dead letter queue configured with monitoring
- [ ] Distributed tracing in place (OpenTelemetry)
- [ ] Outbox pattern used for transactional events (if needed)
- [ ] Consumer failure handling defined (retry, DLQ, alert)
- [ ] Event catalog maintained (what events exist, who produces/consumes)
