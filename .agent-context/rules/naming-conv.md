# Naming Conventions — The "No Lazy Names" Standard

> If your variable name needs a comment to explain it, the name is wrong.

## Universal Rules (All Languages)

### Variables: Nouns That Tell a Story
```
❌ BANNED                    ✅ REQUIRED
─────────────────────────────────────────────
d                           durationInSeconds
data                        userProfilePayload
res                         httpResponse
temp                        unsortedItems
val                         discountPercentage
info                        orderSummary
item                        cartLineItem
list                        activeSubscriptions
obj                         paymentConfiguration
```

**Rule:** A variable name must answer "WHAT is this?" without reading surrounding code.

### Functions: Verbs That Declare Intent
```
❌ BANNED                    ✅ REQUIRED
─────────────────────────────────────────────
process()                   validatePaymentDetails()
handle()                    routeIncomingWebhook()
doStuff()                   calculateShippingCost()
run()                       executeScheduledCleanup()
getData()                   fetchActiveUsersByRegion()
check()                     isEligibleForDiscount()
```

**Rule:** A function name must answer "WHAT does this do?" as a verb phrase. Generic verbs like `process`, `handle`, `manage` are BANNED unless suffixed with a specific noun (e.g., `handlePaymentFailure`).

### Booleans: is/has/can/should Prefix
```
❌ BANNED                    ✅ REQUIRED
─────────────────────────────────────────────
active                      isActive
logged                      isLoggedIn
admin                       hasAdminRole
edit                        canEditDocument
visible                     shouldRenderSidebar
```

**Rule:** Boolean variables MUST use `is`, `has`, `can`, or `should` prefix. No exceptions.

### Constants: SCREAMING_SNAKE for True Constants
```
❌ BANNED                    ✅ REQUIRED
─────────────────────────────────────────────
maxRetries = 3              MAX_RETRY_COUNT = 3
timeout = 5000              REQUEST_TIMEOUT_MS = 5000
apiUrl = "..."              API_BASE_URL = "..."
```

**Rule:** Use SCREAMING_SNAKE_CASE for compile-time constants and config values. Include the unit in the name when applicable (`_MS`, `_BYTES`, `_COUNT`).

### Single-Letter Variables
**BANNED.** With exactly ONE exception:

```
// ALLOWED: Classic loop counter in simple iterations
for (let i = 0; i < items.length; i++) { ... }

// BANNED: Everything else
const x = getPrice();        // ❌ What is x?
const n = users.length;      // ❌ Use userCount
arr.map(v => v.id);          // ❌ Use user => user.id
```

---

## File & Directory Naming

### Files
| Type | Convention | Example |
|------|-----------|---------|
| Component (React/Vue) | PascalCase | `PaymentForm.tsx` |
| Module/Service | camelCase or kebab-case | `paymentService.ts` or `payment-service.ts` |
| Utility | camelCase or kebab-case | `formatCurrency.ts` or `format-currency.ts` |
| Test | Same as source + `.test`/`.spec` | `paymentService.test.ts` |
| Type/Interface | PascalCase | `PaymentTypes.ts` |
| Constant file | SCREAMING_SNAKE or kebab-case | `constants.ts` or `api-endpoints.ts` |
| Config | kebab-case | `database-config.ts` |

**Rule:** Pick ONE convention per project and enforce it everywhere. Mixing `camelCase` and `kebab-case` in the same project is a code smell.

### Directories
- Always `kebab-case`: `user-management/`, `payment-processing/`
- Never PascalCase for directories (except component folders in React convention)
- No abbreviations: `auth/` → `authentication/` (unless universally understood like `api/`, `db/`)

---

## Abbreviation Policy

### Allowed (Universal)
`id`, `url`, `api`, `db`, `http`, `io`, `ui`, `dto`, `config`, `env`, `auth`, `admin`, `src`, `lib`, `pkg`, `cmd`, `ctx`, `err`, `req`, `res` (in HTTP handler context only)

### Banned
Everything else. Spell it out:
```
❌ usr → ✅ user
❌ cnt → ✅ count
❌ mgr → ✅ manager
❌ btn → ✅ button
❌ msg → ✅ message
❌ impl → ✅ implementation
❌ calc → ✅ calculate
❌ proc → ✅ process
```

---

## The Naming Decision Tree

```
Is it a boolean?
  → Yes → Add is/has/can/should prefix
  → No ↓

Is it a function?
  → Yes → Start with a verb (fetch, create, validate, calculate, is, has)
  → No ↓

Is it a constant?
  → Yes → SCREAMING_SNAKE_CASE with unit suffix
  → No ↓

Is it a class/type/interface?
  → Yes → PascalCase, noun, no prefix (not IUser, not UserInterface)
  → No ↓

It's a variable
  → Descriptive noun, camelCase
  → Must be understandable without context
```
