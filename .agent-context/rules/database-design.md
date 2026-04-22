# Database Design — Schema Is Your Foundation

> A poorly designed schema is a bug factory.
> You can fix bad code in hours. A bad schema takes weeks.

## Normalization Rules

### Third Normal Form (3NF) is the Default

```
❌ BANNED: Flat tables with repeated data
Users:
  | id | name  | order_id | order_total | product_name |
  | 1  | Jane  | 101      | 99.99       | Widget       |
  | 1  | Jane  | 102      | 49.99       | Gadget       |
  → name is duplicated, update anomalies guaranteed

✅ REQUIRED: Normalized to 3NF
Users:    | id | name  | email          |
Orders:   | id | user_id | total | status |
Products: | id | name   | price |
OrderItems: | order_id | product_id | quantity |
  → Each fact is stored exactly once
```

### When to Denormalize

Denormalization is allowed ONLY with documented justification:

1. **Read-heavy query** that joins 4+ tables and is called >1000x/sec
2. **Reporting/analytics** where query speed matters more than write consistency
3. **CQRS read model** that is purpose-built for a specific query

```
REQUIRED for every denormalization:
- Document WHY (link to performance evidence)
- Document HOW it stays in sync (trigger, event, scheduled job)
- Add a comment in the schema: "Denormalized for [query name], synced by [mechanism]"
```

---

## Indexing Strategy

### Rules of Indexing

1. **Every foreign key gets an index** — joins on unindexed FKs are full table scans
2. **Every WHERE clause in a frequent query gets evaluated** — if the column appears in WHERE and the table has >10K rows, consider an index
3. **Composite indexes matter** — `INDEX(status, created_at)` ≠ `INDEX(created_at, status)`. Column order follows the query pattern (most selective first, or matching WHERE + ORDER BY)
4. **Covering indexes** — include frequently selected columns to avoid table lookups

### What to Index

| Pattern | Index Type | Example |
|---------|-----------|---------|
| FK lookups | B-tree (default) | `orders.user_id` |
| Status + date filters | Composite | `INDEX(status, created_at)` |
| Full-text search | Full-text / GIN | `products.description` |
| JSON queries | GIN (PostgreSQL) | `metadata->>'type'` |
| Unique constraints | Unique | `users.email` |
| Geospatial | Spatial / GiST | `locations.coordinates` |

### What NOT to Index

- Columns with very low cardinality on small tables (`is_active` with 2 values on 100 rows)
- Tables with <1000 rows (index overhead > benefit)
- Write-heavy tables where every INSERT updates 10+ indexes
- Columns never used in WHERE, JOIN, or ORDER BY

### Index Monitoring

```
REQUIRED:
- Identify unused indexes monthly → DROP them (they slow writes)
- Identify missing indexes → EXPLAIN ANALYZE on slow queries
- Track index size vs table size → alarming if indexes > 3x table size
```

---

## Migration Standards

### Rules

1. **Every schema change is a migration** — never modify production schemas manually
2. **Migrations are versioned and sequential** — `001_create_users.sql`, `002_add_email_index.sql`
3. **Migrations are idempotent** — running twice produces the same result
4. **Migrations are reversible** — every UP has a DOWN (or document why rollback is impossible)
5. **Migrations run in CI** — test against a real database, not just syntax checks

### Safe Migration Patterns

```
✅ SAFE (no downtime):
1. ADD COLUMN with default (nullable or with DEFAULT)
2. CREATE INDEX CONCURRENTLY
3. ADD new table
4. Rename via view + synonym (transitional)

❌ DANGEROUS (requires planned downtime or careful orchestration):
1. DROP COLUMN (deploy code changes removing column usage FIRST)
2. RENAME COLUMN (use gradual rename: add new → copy data → remove old)
3. ALTER COLUMN TYPE (may lock table on large datasets)
4. DROP TABLE (ensure no code references remain)
```

### The Expand-Contract Pattern

For breaking schema changes in zero-downtime deployments:

```
Phase 1 (Expand): Add new column/table alongside old one
   → Code writes to BOTH old and new
Phase 2 (Migrate): Backfill data from old to new
   → Verify data consistency
Phase 3 (Contract): Remove old column/table
   → Code reads/writes only new
```

---

## Data Type Selection

### Use the Right Type

| Data | ❌ Wrong | ✅ Right | Why |
|------|---------|---------|-----|
| Money | `FLOAT` | `DECIMAL(19,4)` or integer cents | Floating point arithmetic is imprecise |
| UUID | `VARCHAR(36)` | `UUID` native type | 16 bytes vs 36 bytes, indexing is faster |
| Timestamps | `VARCHAR` | `TIMESTAMPTZ` | Timezone-aware, sortable, comparable |
| IP addresses | `VARCHAR(45)` | `INET` (PostgreSQL) | Validation built-in, range queries |
| Boolean | `INT` (0/1) | `BOOLEAN` | Semantic clarity |
| Enums | `VARCHAR` | Database ENUM or CHECK constraint | Prevents invalid values |
| JSON blobs | `TEXT` | `JSONB` (PostgreSQL) | Indexable, queryable, validated |

### Column Naming

```
✅ REQUIRED:
- snake_case for all column names
- Descriptive: created_at, updated_at, deleted_at (not ts, mod, del)
- Foreign keys: {referenced_table_singular}_id (e.g., user_id, order_id)
- Boolean columns: is_active, has_verified_email, can_edit
- Timestamps: {verb}_at (created_at, verified_at, shipped_at)
- Amounts: {noun}_amount or {noun}_cents (total_amount, tax_cents)
```

---

## Query Design Rules

### Pagination (Mandatory for Lists)

```
❌ BANNED:
SELECT * FROM orders;
-- Returns 2 million rows, OOM crash

✅ REQUIRED: Offset pagination (simple, okay for < 100K rows)
SELECT * FROM orders ORDER BY id LIMIT 20 OFFSET 40;

✅ PREFERRED: Cursor pagination (performant at any scale)
SELECT * FROM orders WHERE id > :last_seen_id ORDER BY id LIMIT 20;
```

**Rule:** Use cursor-based pagination for tables > 100K rows. Offset pagination degrades linearly with OFFSET value.

### Soft Deletes vs Hard Deletes

```
Use soft deletes (deleted_at column) when:
- Legal/compliance requires data retention
- Users might want to "undelete"
- Related data would break without the parent record

Use hard deletes when:
- GDPR/privacy requires actual data removal
- Data has no business value after deletion
- Storage cost of keeping data outweighs benefit

If soft deleting:
- Add deleted_at to ALL queries: WHERE deleted_at IS NULL
- Add a partial index: WHERE deleted_at IS NULL (for performance)
- Schedule periodic hard-delete of old soft-deleted records
```

---

## The Database Design Checklist

Before any schema goes to production:

- [ ] Schema is normalized to 3NF (denormalization documented if present)
- [ ] All foreign keys have indexes
- [ ] Primary keys use appropriate type (UUID or BIGINT)
- [ ] Timestamps use TIMESTAMPTZ (not VARCHAR)
- [ ] Money uses DECIMAL or integer cents (never FLOAT)
- [ ] Migration is versioned, reversible, and tested in CI
- [ ] All list queries have LIMIT (pagination implemented)
- [ ] Indexes justified with EXPLAIN ANALYZE on expected queries
- [ ] Column naming follows convention (snake_case, descriptive)
- [ ] Soft delete vs hard delete decision documented
