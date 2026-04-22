# Error Handling — Never Swallow, Always Context

> A swallowed error is a silent production incident waiting to happen.
> When it explodes at 3 AM, you won't know where to look.

## The Three Commandments

1. **Never swallow an error.** Every error must be logged, re-thrown, or explicitly handled.
2. **Always add context.** A stack trace is not enough — include WHAT was happening and WITH WHAT data.
3. **Fail fast at boundaries.** Validate early, reject bad data before it travels deep into the system.

---

## Swallowed Error Detection (Instant Rejection)

```
❌ DEATH PENALTY: Empty catch block
try {
  await processPayment(order);
} catch (error) {
  // silently swallowed — payment may have failed, user has no idea
}

❌ DEATH PENALTY: Catch and log only (no re-throw or recovery)
try {
  await processPayment(order);
} catch (error) {
  console.log('error:', error);  // Logged to a void nobody reads
  // Execution continues as if nothing happened
}

✅ CORRECT: Handle, log with context, re-throw or recover
try {
  await processPayment(order);
} catch (error) {
  logger.error('Payment processing failed', {
    orderId: order.id,
    userId: order.userId,
    amount: order.total,
    error: error instanceof Error ? error.message : String(error),
  });
  throw new PaymentFailedError(order.id, { cause: error });
}
```

---

## Typed Error Codes

### Rule: Use Explicit Error Types, Not Generic Errors

```
❌ BANNED: Generic errors
throw new Error('Not found');
throw new Error('Permission denied');
throw new Error('Invalid input');

✅ REQUIRED: Typed, domain-specific errors
throw new NotFoundError('User', userId);
throw new ForbiddenError('Cannot delete other user\'s order');
throw new ValidationError('Email format is invalid', { field: 'email' });
```

### Error Class Pattern (Any Language)
```typescript
// Base application error
class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number,
    public readonly context?: Record<string, unknown>,
  ) {
    super(message);
    this.name = this.constructor.name;
  }
}

// Specific errors
class NotFoundError extends AppError {
  constructor(resource: string, id: string | number) {
    super(`${resource} not found: ${id}`, 'NOT_FOUND', 404, { resource, id });
  }
}

class ValidationError extends AppError {
  constructor(message: string, context?: Record<string, unknown>) {
    super(message, 'VALIDATION_ERROR', 400, context);
  }
}

class ForbiddenError extends AppError {
  constructor(reason: string) {
    super(reason, 'FORBIDDEN', 403);
  }
}
```

---

## Structured Logging

### Rule: Logs Must Include Context

```
❌ USELESS:
logger.error('Something went wrong');
logger.info('Processing...');
console.log(error);

✅ USEFUL:
logger.error('Order processing failed', {
  traceId: req.traceId,
  userId: currentUser.id,
  orderId: order.id,
  action: 'processOrder',
  error: error.message,
  stack: error.stack,
});

logger.info('Payment completed', {
  traceId: req.traceId,
  orderId: order.id,
  amount: payment.amount,
  provider: payment.provider,
  durationMs: Date.now() - startTime,
});
```

### Required Log Fields
| Field | When | Purpose |
|-------|------|---------|
| `traceId` / `requestId` | Always (in request context) | Correlate logs across services |
| `userId` | When authenticated | Who triggered the action |
| `action` | Always | What was happening |
| `error` + `stack` | On errors | What went wrong |
| `durationMs` | On slow operations | Performance visibility |

---

## Error Response Format (APIs)

### Rule: NEVER Leak Internal Details

```
❌ BANNED response to client:
{
  "error": "ER_NO_SUCH_TABLE: Table 'mydb.user_sessions' doesn't exist",
  "stack": "Error: at Query.execute (/app/node_modules/mysql..."
}
// Congratulations, you just told the attacker your DB name and framework

✅ REQUIRED response to client:
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred. Please try again.",
    "traceId": "abc-123-def"
  }
}
// Internal details go to your logs, not to the client
```

### Error Response Mapping
| Internal Error | HTTP Status | Client Message |
|---------------|-------------|----------------|
| `ValidationError` | 400 | Show specific field errors |
| `AuthenticationError` | 401 | "Invalid credentials" (never specify which field) |
| `ForbiddenError` | 403 | "Insufficient permissions" |
| `NotFoundError` | 404 | "Resource not found" |
| `ConflictError` | 409 | "Resource already exists" |
| `RateLimitError` | 429 | "Too many requests" |
| Unhandled errors | 500 | "Internal error" + traceId for support |

---

## Fail-Fast at Boundaries

```
// ✅ Validate at the entry point, fail before going deeper
async function createOrder(req: Request) {
  // Step 1: Validate input IMMEDIATELY
  const parsed = CreateOrderSchema.safeParse(req.body);
  if (!parsed.success) {
    throw new ValidationError('Invalid order data', parsed.error.flatten());
  }

  // Step 2: Now use the validated, typed data
  const order = await orderService.create(parsed.data);
  return order;
}

// ❌ Don't let bad data travel deep before failing
async function createOrder(req: Request) {
  const data = req.body;  // Unvalidated!
  const order = await orderService.create(data);
  // Service calls repository, repository tries to insert...
  // Database throws a cryptic constraint violation 5 layers deep
}
```

---

## Retry Strategy

When retrying failed operations:

1. **Only retry transient errors** (network timeouts, 503s) — NEVER retry validation errors or auth failures
2. **Use exponential backoff** — 100ms → 200ms → 400ms → 800ms
3. **Set a maximum retry count** (typically 3)
4. **Log every retry attempt** with attempt number and error
5. **Add jitter** to prevent thundering herd

```typescript
async function withRetry<T>(
  operation: () => Promise<T>,
  maxAttempts: number = 3,
  baseDelayMs: number = 100,
): Promise<T> {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      if (attempt === maxAttempts || !isTransientError(error)) {
        throw error;
      }
      const delay = baseDelayMs * Math.pow(2, attempt - 1) + Math.random() * 100;
      logger.warn('Retrying operation', { attempt, maxAttempts, delayMs: delay });
      await sleep(delay);
    }
  }
  throw new Error('Unreachable');
}
```
