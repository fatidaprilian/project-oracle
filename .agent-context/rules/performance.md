# Performance — Measure Before You Optimize

> Premature optimization is the root of all evil.
> But ignoring obvious performance traps is just incompetence.

## The Performance Prime Directive

**Do NOT optimize without evidence.** CPU time is cheap. Developer time is expensive.

## Context-Triggered Strict Audit Mode

Strict performance audits must activate automatically for:
- review requests
- PR-intent workflows (pull request preparation and merge readiness)
- major feature completion

Small edits stay in lightweight mode by default to avoid unnecessary heavy checks.
Users can always force strict performance mode manually.

BUT — there are patterns so obviously bad that they don't need benchmarks to reject.
Those are listed below as **Death Penalties**.

---

## Death Penalties (Always Reject)

### 1. N+1 Queries
```
❌ INSTANT REJECTION:
const users = await db.query('SELECT * FROM users');
for (const user of users) {
  user.orders = await db.query('SELECT * FROM orders WHERE user_id = ?', [user.id]);
  // This runs 1 + N queries. For 1000 users = 1001 database round trips.
}

✅ REQUIRED:
const users = await db.query('SELECT * FROM users');
const userIds = users.map(u => u.id);
const orders = await db.query('SELECT * FROM orders WHERE user_id = ANY($1)', [userIds]);
// 2 queries total, regardless of user count
// Or use ORM eager loading / DataLoader pattern
```

**Rule:** If you see a query inside a loop, it is almost certainly an N+1 bug. Fix it with JOINs, batch queries, or DataLoader.

### 2. Unbounded Queries
```
❌ INSTANT REJECTION:
const allUsers = await db.query('SELECT * FROM users');
// In production, "users" table has 2 million rows. Enjoy your OOM.

✅ REQUIRED:
const users = await db.query('SELECT * FROM users LIMIT $1 OFFSET $2', [pageSize, offset]);
// Or use cursor-based pagination for large datasets
```

**Rule:** EVERY query that returns a list MUST have a LIMIT. APIs MUST support pagination. Default page size: 20-50.

### 3. SELECT * in Production
```
❌ BANNED:
SELECT * FROM users;  -- Fetches 30 columns when you need 3

✅ REQUIRED:
SELECT id, email, display_name FROM users;
```

**Rule:** Select only the columns you need. `SELECT *` wastes bandwidth, memory, and makes schema changes dangerous.

### 4. Synchronous I/O in Async Context
```
❌ BANNED:
// In an async Node.js server
const data = fs.readFileSync('/path/to/file');
const result = execSync('some-command');

✅ REQUIRED:
const data = await fs.promises.readFile('/path/to/file');
const result = await exec('some-command');
```

**Rule:** In async environments (Node.js, Python asyncio), NEVER block the event loop with synchronous I/O.

---

## Optimize Only With Evidence

For everything else, follow this protocol:

### Step 1: Measure
```
// Use profiling tools, not guesses
console.time('operation');
await heavyOperation();
console.timeEnd('operation');

// Use proper APM: Datadog, New Relic, OpenTelemetry
```

### Step 2: Identify the Bottleneck
- Is it CPU? Memory? I/O? Network?
- Don't optimize CPU when the bottleneck is a slow database query

### Step 3: Optimize the Bottleneck (Not Everything Else)
- Fix the slowest thing first
- Re-measure after each change
- Stop when performance meets requirements

---

## Caching Rules

### When to Cache
- Data that is read frequently, written rarely
- Expensive computations that produce the same result for same inputs
- External API responses (respect their cache headers)

### When NOT to Cache
- Data that changes every request
- Small, fast queries (cache overhead > query time)
- When you can't define a clear invalidation strategy

### The Caching Devil's Triangle
You can have 2 of 3:
1. **Fresh data** (always up-to-date)
2. **Fast reads** (sub-millisecond)
3. **Simple code** (no cache layer)

Pick your 2 and document the trade-off.

### Invalidation Strategy (MANDATORY)
```
❌ BANNED:
cache.set('users', data);  // When does this expire? Who invalidates it? Nobody knows.

✅ REQUIRED:
cache.set('users:active', data, { ttl: 300 });  // 5 min TTL, explicit key
// AND document: "Invalidated on user.created, user.deleted, user.deactivated events"
```

**Rule:** NEVER add a cache without documenting the invalidation strategy. "We'll figure it out later" means "we'll have stale data in production."

---

## Connection Management

1. **Use connection pools** — never open/close connections per request
2. **Set pool limits** — max connections based on infrastructure, not infinity
3. **Implement timeouts** — connection timeout, query timeout, request timeout
4. **Handle pool exhaustion** — fail fast with clear error, don't queue forever

---

## Frontend Performance (When Applicable)

1. **Lazy load** routes and heavy components
2. **Debounce** search inputs and scroll handlers (300ms minimum)
3. **Virtualize** long lists (don't render 10,000 DOM nodes)
4. **Optimize images** — WebP/AVIF, responsive sizes, lazy loading
5. **Bundle analysis** — if your JS bundle exceeds 200KB gzipped, investigate

---

## The Performance Decision Framework

```
Is it a known Death Penalty pattern (N+1, unbounded, SELECT *, sync I/O)?
  → Yes → Fix it now, no measurement needed
  → No ↓

Is there a measurable performance problem?
  → No → Don't optimize. Ship it.
  → Yes ↓

Have you identified the specific bottleneck?
  → No → Profile first
  → Yes → Optimize ONLY that bottleneck, re-measure, stop when sufficient
```
