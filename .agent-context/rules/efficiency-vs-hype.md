# Efficiency vs. Hype — Choose Stable, Not Shiny

> Every dependency is a liability. Every `npm install` is a trust decision.
> The best dependency is the one you don't need.

## Latest-Compatible-First Rule

- Start from the latest stable compatible dependency version, not an outdated tutorial version.
- If the framework has an official scaffolder or setup command that produces current defaults, prefer that path over manually assembling stale `package.json` entries one by one.
- Only step down to an older dependency version after documenting the exact compatibility, runtime, platform, or ecosystem reason.
- Treat release notes, official docs, and framework migration guides as the primary source of truth for dependency setup.

## The Dependency Decision Framework

Before adding ANY dependency, answer these 5 questions:

### 1. Can You Do It Without a Library? (The stdlib-first Rule)
```
❌ OVER-ENGINEERING:
npm install is-odd        # 1 line of code: n % 2 !== 0
npm install left-pad      # Already in String.prototype.padStart
npm install is-number     # typeof x === 'number' && !isNaN(x)
npm install array-flatten # Array.prototype.flat() exists since ES2019

✅ USE THE LANGUAGE:
const isOdd = (n: number) => n % 2 !== 0;
const padded = str.padStart(10, '0');
const flat = nested.flat(Infinity);
```

**Dependency Defense:** If the user asks to install a new library, or if you feel the need to use one, evaluate it against the "stdlib-first" rule. If the functionality can be implemented safely in under 20 lines of code, write it yourself. If a dependency is strictly necessary, you MUST justify it by providing its bundle size, maintenance status, why the standard library is insufficient, and why the chosen version is the latest stable compatible option.

### 2. Is It Maintained? (The Pulse Check)
| Signal | 🟢 Healthy | 🔴 Dead |
|--------|-----------|---------|
| Last commit | < 6 months ago | > 2 years ago |
| Open issues | Actively triaged | 500+ unread |
| Downloads/week | Growing or stable | Declining |
| Bus factor | > 3 maintainers | 1 maintainer, inactive |
| Security | No known CVEs | Unpatched vulnerabilities |

**Rule:** If a library has a bus factor of 1 and no commit in 12+ months, it is a risk. Find an alternative or vendor-fork it.

### 3. What's the Cost? (The Weight Check)
```
Before: npm install moment     # 289KB minified, entire library for date formatting
After:  npm install date-fns   # 12KB for just the functions you use (tree-shakeable)
Better: Intl.DateTimeFormat    # 0KB — built into the runtime
```

**Rule:** Check the bundle impact. Use [bundlephobia.com](https://bundlephobia.com) for JS packages. If a library adds > 50KB to your bundle for a simple feature, find a lighter alternative or implement it yourself.

### 4. Is It the Community Standard? (The Ecosystem Rule)
Prefer packages that the ecosystem has settled on:

| Need | ✅ Standard | ❌ Avoid |
|------|-----------|---------|
| HTTP client (Node) | `undici` (built-in) / native `fetch` / `ky` | `axios` (declining, CVE-2025-58754, bloated) |
| Validation | `zod` | `joi` (heavier), `yup` (less type-safe) |
| ORM (Node) | `prisma`, `drizzle` | `sequelize` (legacy API), `typeorm` (decorator hell) |
| Date handling | `date-fns`, `dayjs`, `Temporal` (when stable) | `moment` (deprecated, massive) |
| Testing | `vitest` (new projects), `jest` (existing) | `mocha` + `chai` + `sinon` (3 deps for what 1 does) |
| Password hashing | `argon2` (OWASP primary), `bcrypt` (legacy) | Custom crypto (NEVER) |
| Env loading | `dotenv` (if needed) | Custom `.env` parser |

**Note:** These are current recommendations as of March 2026. Evaluate against this framework; don't blindly follow.

### 5. Can You Remove It Later? (The Exit Strategy)
```
❌ HIGH LOCK-IN:
// Decorators from a specific framework scattered across 200 files
@Controller() @Injectable() @Guard() // In every file — framework is your entire architecture

✅ LOW LOCK-IN:
// Framework stays at the edges; business logic is framework-free
// Switching from Express to Fastify only changes the transport layer
```

**Rule:** Wrap external dependencies that touch > 5 files. If you need to replace a library, it should only affect the wrapper, not your entire codebase.

---

## The Hype Trap (AI-Generated Code Alert)

AI agents love suggesting trendy libraries because they appear frequently in training data. Watch for:

### Red Flags
1. **"Just install X"** without explaining why → ASK: Can I do this with the stdlib?
2. **Library does one thing** that's 5 lines of code → REJECT: Write it yourself
3. **Library is in alpha/beta** with < 1 year of releases → REJECT: Not production-ready
4. **Library has a cooler API** but the current one works fine → REJECT: "Cool" is not a business requirement
5. **"Everyone is using it"** → SO WHAT: Popularity is not a quality signal

### The Agent Must Justify Dependencies
When an AI agent suggests adding a new dependency, it MUST provide:
```
📦 DEPENDENCY JUSTIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Package: [name@version]
Purpose: [what it does in 1 sentence]
Stdlib Alternative: [why it's insufficient — or "none"]
Bundle Size: [minified + gzipped]
Maintenance: [last release date, maintainer count]
Version Source: [official docs, release notes, or framework reference]
Lock-in Risk: [low/medium/high — how many files would it touch]
Exit Strategy: [how to remove it if needed]
Fallback Reason: [only required when not using the latest stable compatible version]
```

---

## Dependency Update Strategy

1. **Start from latest stable compatible versions** — older versions need a written reason
2. **Prefer official framework setup flows** when they yield newer, canonical dependency sets
3. **Pin exact versions** in lockfiles (already default with package-lock.json, bun.lockb)
4. **Review changelogs** before major updates — never blindly `npm update`
5. **Update in isolation** — one dependency per PR, with tests passing
6. **Security patches immediately** — don't wait for the sprint
7. **Monthly audit** — run `npm audit` / `bun audit` and address findings

---

## The Zero-Dependency Ideal

The best packages are those with zero or minimal dependencies themselves:
- `zod` — 0 dependencies ✅
- `date-fns` — 0 dependencies ✅
- `nanoid` — 0 dependencies ✅
- `bcrypt` — 1 native dependency (justified for crypto) ✅

A package that pulls in 50 transitive dependencies for a simple feature is a supply chain attack waiting to happen.

---

## Quick Decision Tree

```
Do I need this functionality?
  → No → Don't install anything
  → Yes ↓

Can I write it in < 20 lines?
  → Yes → Write it yourself
  → No ↓

Does the language/runtime provide it?
  → Yes → Use the built-in
  → No ↓

Is there a well-maintained, lightweight, community-standard package?
  → Yes → Install it, add justification comment
  → No → Build a minimal internal implementation, consider vendoring
```
