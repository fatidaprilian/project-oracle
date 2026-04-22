# Security — Trust Nothing, Validate Everything

> Every user is a potential attacker. Every input is a potential exploit.
> You are not paranoid — you are professional.

## The Zero Trust Input Rule

**ALL data crossing a system boundary is untrusted until validated.**

## Context-Triggered Strict Audit Mode

Strict security audits must activate automatically for:
- review requests
- PR-intent workflows (pull request preparation and merge readiness)
- major feature completion

Small edits stay in lightweight mode by default to avoid unnecessary heavy checks.
Users can always force strict security mode manually.

System boundaries include:
- HTTP request bodies, query params, headers, cookies
- URL path parameters
- File uploads
- WebSocket messages
- Queue/event payloads
- Environment variables (at startup)
- Database query results (yes, even these — data could be corrupted)
- Third-party API responses

### Validation Protocol
```
External Input → Schema Validation (Zod/Pydantic/Bean Validation) → Typed Internal Object

NEVER:
External Input → Direct use in business logic
External Input → Direct use in database query
External Input → Direct interpolation into strings
```

---

## Injection Prevention

### SQL Injection — Parameterized Queries Only
```
❌ DEATH PENALTY:
const query = `SELECT * FROM users WHERE id = ${userId}`;
const query = "SELECT * FROM users WHERE name = '" + name + "'";

✅ ALWAYS:
const user = await db.query('SELECT * FROM users WHERE id = $1', [userId]);
const user = await prisma.user.findUnique({ where: { id: userId } });
```

**Rule:** NEVER concatenate or interpolate user input into SQL strings. Use parameterized queries or ORMs. No exceptions. Not even "just for testing."

### Command Injection
```
❌ DEATH PENALTY:
exec(`convert ${filename} output.png`);

✅ ALWAYS:
execFile('convert', [filename, 'output.png']);
```

**Rule:** Never pass user input to shell commands via string interpolation. Use argument arrays.

### XSS Prevention
```
❌ BANNED:
element.innerHTML = userInput;
dangerouslySetInnerHTML={{ __html: userInput }};

✅ REQUIRED:
element.textContent = userInput;
// Or sanitize with DOMPurify if HTML is absolutely needed
```

**Rule:** Default to text content. Only use HTML injection with explicit sanitization AND a code comment explaining WHY.

---

## Secret Management

### Rule: ZERO Secrets in Code

```
❌ INSTANT REJECTION:
const API_KEY = "sk-abc123def456";
const DB_PASSWORD = "supersecret";
const JWT_SECRET = "my-jwt-secret";
// Even in .env.example with real values

✅ REQUIRED:
const API_KEY = process.env.API_KEY;      // Read from environment
const DB_URL = process.env.DATABASE_URL;   // Injected at runtime
```

### .env Files
- `.env` → NEVER committed (must be in `.gitignore`)
- `.env.example` → Committed with placeholder values ONLY (`API_KEY=your-api-key-here`)
- `.env.local` → NEVER committed
- `.env.test` → May be committed with TEST-ONLY non-secret values

### Secret Rotation
If a secret is accidentally committed:
1. Rotate the secret IMMEDIATELY (not after the PR is merged — NOW)
2. Remove from git history (`git filter-branch` or BFG)
3. Add to `.gitignore`
4. Document the incident

---

## Authentication & Authorization

### Authentication Rules
1. Never implement custom auth crypto — use established libraries (argon2, bcrypt, Passport, NextAuth)
2. Hash passwords with **argon2id** (OWASP primary recommendation) — bcrypt only for legacy systems
   - Argon2id: minimum 19 MiB memory, 2 iterations, 1 parallelism
   - bcrypt: minimum cost 12 (legacy systems only — limited to 72 bytes, no memory-hardness)
   - NEVER: MD5, SHA1, plain SHA256, or PBKDF2 without FIPS requirement
3. Use constant-time comparison for tokens and hashes
4. Implement rate limiting on auth endpoints (max 5 attempts per minute per IP)
5. Session tokens must be cryptographically random (≥ 256 bits)

### Authorization Rules
1. **Default deny** — if no rule grants access, deny
2. **Server-side only** — NEVER trust client-side role checks for security
3. Check authorization at the service layer, not just the controller
4. Log all authorization failures with context (userId, resource, action)

```
❌ BANNED: Client-side only authorization
if (user.role === 'admin') { showDeleteButton(); }
// Attacker just changes user.role in devtools

✅ REQUIRED: Server-side enforcement
// Controller checks auth, service enforces business rules
async deleteUser(requesterId: string, targetUserId: string) {
  const requester = await this.userRepo.findById(requesterId);
  if (!requester || requester.role !== Role.ADMIN) {
    throw new ForbiddenError('Insufficient permissions');
  }
  // ... proceed with deletion
}
```

---

## HTTP Security Headers

Every web application MUST include:
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; script-src 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

### CORS
- NEVER use `Access-Control-Allow-Origin: *` in production
- Whitelist specific origins
- Be explicit about allowed methods and headers

---

## File Upload Security

1. Validate MIME type server-side (not just file extension)
2. Set maximum file size limits
3. Generate random filenames — never use user-provided filenames
4. Store uploads outside the web root
5. Scan for malware if accepting documents

---

## Supply Chain Security (OWASP 2025 A03)

1. **Pin all dependency versions** — use lockfiles, never `*` ranges in production
2. **Audit dependencies regularly** — `npm audit`, `pip audit`, `composer audit`
3. **Verify package integrity** — check checksums, use signed packages where available
4. **Minimize dependency trees** — fewer transitive dependencies = smaller attack surface
5. **Monitor for CVEs** — automate vulnerability scanning in CI (Dependabot, Snyk, Trivy)
6. **Review new dependencies** — check maintainer history, download trends, and bus factor before adding

---

## .gitignore Enforcement (Mandatory)

**If the user's INTENT is to create a new project, push to GitHub, or initialize source control, you MUST generate or verify a `.gitignore` file exists.**

### Minimum Required Entries
```gitignore
# ── Secrets & Environment ──
.env
.env.local
.env.*.local
.env.production
.env.staging

# ── Dependencies ──
node_modules/
vendor/
venv/
.venv/
__pycache__/
.gradle/
target/
bin/  # Go binaries
pkg/

# ── Build Output ──
dist/
build/
out/
*.min.js
*.min.css
.next/
.nuxt/
.output/

# ── IDE & Editor ──
.idea/
.vscode/settings.json
.vscode/launch.json
*.swp
*.swo
*~

# ── OS Artifacts ──
.DS_Store
Thumbs.db
Desktop.ini
*.lnk

# ── Logs ──
*.log
npm-debug.log*
yarn-debug.log*
pnpm-debug.log*

# ── Testing & Coverage ──
coverage/
.nyc_output/
*.lcov

# ── Runtime & Backup Data ──
*.pid
*.seed
*.pid.lock
.agentic-backup/

# ── Secrets & Keys ──
*.pem
*.key
*.p12
*.jks
*.keystore
```

### Rules
1. **NEVER commit `.env`** — only `.env.example` with placeholder values
2. **Check for leaks before push** — `git diff --cached --name-only | grep -E '\.(env|pem|key)$'` should return empty
3. **If the project has NO `.gitignore`**, create one immediately before any `git add`
4. **Extend per-stack** — add language-specific patterns (e.g., `__pycache__/` for Python, `target/` for Java/Rust, `.gradle/` for Kotlin)
5. **Reference**: See `.agent-context/rules/git-workflow.md` for the full `.gitignore Standards` section

### MUST Commit (Whitelist)
```
.env.example           # Template with placeholder values ONLY
.editorconfig          # Consistent formatting across IDEs
.gitignore             # This file itself
docker-compose.yml     # Dev environment definition
Makefile / Taskfile    # Standard dev commands
```

---

## The Security Checklist (Quick Reference)

Before any code is "done", verify:

- [ ] All inputs validated at boundaries with schemas
- [ ] No string concatenation in queries/commands
- [ ] No secrets in source code
- [ ] `.gitignore` exists and covers `.env`, `node_modules/`, build output, and IDE files
- [ ] Authentication uses established libraries
- [ ] Password hashing uses argon2id (or bcrypt for legacy)
- [ ] Authorization enforced server-side
- [ ] Security headers configured
- [ ] CORS properly restricted
- [ ] Rate limiting on sensitive endpoints
- [ ] Error responses don't leak internal details
- [ ] Logging includes security events (login failures, permission denials)
- [ ] Dependencies audited for known vulnerabilities

