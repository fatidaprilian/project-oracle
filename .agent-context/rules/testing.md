# Testing — Prove It Works, Don't Pray

> "It works on my machine" is not a test strategy.
> Untested code is broken code that hasn't been caught yet.

## The Test Pyramid (Enforced)

```
        ╱  E2E   ╲           Few — Slow — Expensive — Fragile
       ╱──────────╲          Test critical user journeys only
      ╱ Integration ╲        Medium — Test module boundaries
     ╱────────────────╲      Database, API contracts, service interactions
    ╱    Unit Tests     ╲    Many — Fast — Cheap — Stable
   ╱──────────────────────╲  Test business logic in isolation
```

### Ratios
- **Unit tests:** 70% — fast, isolated, test business rules
- **Integration tests:** 20% — test boundaries (DB, APIs, modules)
- **E2E tests:** 10% — test critical user flows only

---

## What to Test (And What Not To)

### ✅ ALWAYS Test
- Business logic and calculations
- Input validation rules
- Edge cases (empty arrays, null values, boundary numbers)
- Error handling paths (what happens when things fail)
- State transitions and workflows
- Authorization rules

### ❌ NEVER Test
- Framework internals (don't test that Express routes work)
- Simple getters/setters with no logic
- Third-party library behavior
- Private implementation details (test behavior, not structure)
- Database migrations (verify schema, don't test the migration tool)

---

## Test Naming Convention

### Pattern: `should [expected behavior] when [condition]`

```
❌ BANNED:
test('test1')
test('it works')
test('calculateDiscount')

✅ REQUIRED:
test('should apply 20% discount when order total exceeds $100')
test('should throw ValidationError when email format is invalid')
test('should return empty array when user has no orders')
test('should deny access when user lacks admin role')
```

**Rule:** A reader must understand the expected behavior WITHOUT reading the test body.

---

## Test Structure: AAA Pattern

Every test follows **Arrange → Act → Assert**:

```typescript
test('should calculate shipping as free when order exceeds $50', () => {
  // Arrange — Set up the scenario
  const order = createOrder({ items: [{ price: 60, quantity: 1 }] });

  // Act — Execute the behavior
  const shippingCost = calculateShipping(order);

  // Assert — Verify the outcome
  expect(shippingCost).toBe(0);
});
```

### Rules
- **ONE assert concept per test** (multiple `expect` calls are fine if they test the same concept)
- **No logic in tests** (no if/else, no loops, no try/catch)
- **Tests must be independent** — no shared mutable state, no execution order dependency
- **Tests must be deterministic** — same input = same result, every time

---

## Mocking Rules

### Mock at Boundaries, Not Everywhere

```
❌ OVER-MOCKING (testing implementation, not behavior):
test('should call repository.save exactly once', () => {
  await service.createUser(userData);
  expect(repository.save).toHaveBeenCalledTimes(1);
  // If you refactor to call save differently, the test breaks
  // even though the behavior hasn't changed
});

✅ CORRECT (testing behavior):
test('should persist user and return created user', () => {
  const result = await service.createUser(userData);
  expect(result.id).toBeDefined();
  expect(result.email).toBe(userData.email);
  // You can verify the user exists in the test DB if integration test
});
```

### When to Mock
- External APIs (payment gateways, email services)
- Time-dependent operations (use fake timers)
- Non-deterministic operations (random, UUID)

### When NOT to Mock
- Your own code in the same module ← test the real integration
- Simple utility functions ← use the real thing
- Database in integration tests ← use a test database

---

## Test Data Standards

### Use Factories, Not Copy-Pasted Objects

```
❌ BANNED:
test('should calculate total', () => {
  const order = {
    id: '123',
    userId: '456',
    items: [{ productId: '789', price: 29.99, quantity: 2, name: 'Widget' }],
    status: 'pending',
    createdAt: new Date(),
    updatedAt: new Date(),
    // ... 15 more fields copied from another test
  };
});

✅ REQUIRED:
test('should calculate total', () => {
  const order = createTestOrder({
    items: [createTestItem({ price: 29.99, quantity: 2 })],
  });
  // Factory fills in all other fields with sensible defaults
});
```

### Rules
- Create factory functions for each domain entity
- Factories provide sensible defaults — tests override only relevant fields
- Never use production data in tests
- Use descriptive, obviously-fake data (email: `test-user@example.com`, not `john@gmail.com`)

---

## Coverage Expectations

| Layer | Min Coverage | What to Focus On |
|-------|-------------|------------------|
| Domain / Business Logic | 90%+ | All branching, edge cases, error paths |
| Application / Service | 80%+ | Orchestration flows, error handling |
| Transport / Controller | 60%+ | Input validation, error responses |
| Utilities | 90%+ | All functions and edge cases |

**Rule:** Coverage is a floor, not a goal. 100% coverage with bad tests is worse than 80% coverage with good tests. Focus on testing **behavior and edge cases**, not hitting a number.

---

## When to Skip Tests (Rare)

You may skip tests ONLY for:
- Prototype/spike code (must be labeled `// SPIKE: will be replaced`)
- Pure UI layout (visual testing is better here — use Storybook/Chromatic)
- Generated code (test the generator, not the output)

Everything else gets tested. No excuses.
