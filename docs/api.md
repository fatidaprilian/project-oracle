# Project Oracle API Documentation

## Overview

Project Oracle exposes its strategy intelligence and governance workflows via a REST API built with FastAPI. The API enables:

- Triggering weekly review and governance workflows on-demand or via schedule
- Querying parameter change request status and approvals
- Promoting approved changes to strategy configuration

## Source of Truth

Untuk kontrak API terbaru (schema request/response), gunakan Swagger production:

- https://project-oracle-133425616833.asia-southeast2.run.app/docs

Dokumen ini berfungsi sebagai panduan operasional tambahan.

## Getting Started

### Start the API Server

Development mode (with auto-reload):
```bash
cd src
PYTHONPATH=. python3 run_api.py --reload
```

Production mode (single worker):
```bash
cd src
PYTHONPATH=. python3 run_api.py --host 0.0.0.0 --port 8000
```

Multi-worker production (uvicorn workers):
```bash
cd src
PYTHONPATH=. python3 run_api.py --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000` by default.

## API Endpoints

### Login

```http
POST /api/v1/auth/login
```

No registration flow is required for v1, but user credentials are stored in PostgreSQL table `auth_users` with hashed passwords.

Environment options:
- `ORACLE_AUTH_POSTGRES_DSN` (or fallback `ORACLE_POSTGRES_DSN`)
- `ORACLE_AUTH_HASH_ITERATIONS`

Seed or update user via script:

```bash
PYTHONPATH=src python3 scripts/security/create_auth_user.py --username <USERNAME> --role admin
```

**Request Body:**
```json
{
  "username": "admin-user",
  "password": "<your-password>"
}
```

**Response:**
```json
{
  "access_token": "<jwt-token>",
  "token_type": "bearer",
  "username": "admin-user",
  "role": "admin"
}
```

### Current Auth Session

```http
GET /api/v1/auth/me
```

Requires `Authorization: Bearer <token>`.

**Response:**
```json
{
  "username": "admin-user",
  "role": "admin",
  "auth_source": "jwt"
}
```

### Health Check

```http
GET /health
```

Returns server health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

### Dashboard Signal Surfaces

Dashboard API untuk Oracle saham sekarang mengekspos konteks tambahan berikut:

- `estimated_duration_min_days`
- `estimated_duration_max_days`

Field tersebut muncul pada payload sinyal dan portfolio ketika tersedia, dan harus dibaca sebagai estimasi menuju target dalam **hari bursa**, bukan janji target tercapai pada sesi berikutnya.

### Dashboard Anomaly Radar

```http
GET /api/v1/dashboard/anomalies
```

Response tetap menyertakan `anomalies` sebagai daftar ticker untuk kompatibilitas lama. Field baru `anomaly_details` berisi metadata discovery agar UI bisa membedakan radar biasa dari momentum watch tanpa mengubahnya menjadi sinyal beli.

```json
{
  "anomalies": ["NAYZ.JK"],
  "anomaly_details": [
    {
      "ticker": "NAYZ.JK",
      "lane": "MOMENTUM_WATCH",
      "discovery_score": 52.8,
      "volume_ratio": 11.16,
      "change_pct": 6.9,
      "close_price": 78.0,
      "reason": "VOLUME_EXPANSION_WITH_PRICE_CONFIRMATION",
      "source": "TRADINGVIEW_VOLUME_SCREENER",
      "scanned_at": "2026-04-25T10:45:52Z"
    }
  ]
}
```

Lane saat ini:
- `MOMENTUM_WATCH`: volume mengembang dan harga ikut mengonfirmasi, tetapi belum menjadi sinyal beli.
- `EXTENDED_RISK`: pergerakan sudah terlalu jauh untuk dikejar.
- `RADAR_ONLY`: anomali volume yang masih butuh konfirmasi harga atau punya risiko likuiditas.

### Weekly Workflow

```http
POST /api/v1/weekly-workflow
```

Trigger the complete weekly workflow: run replay, generate AI review packet, produce weekly report, and attempt config promotion.

Optional query parameter:

- `symbol` (contoh: `BTCUSDT`) untuk menjalankan replay dan mencatat request governance per symbol.

**Response:**
```json
{
  "success": true,
  "ai_review_packet_path": "reports/ai-review/2026-W15-ai-review.json",
  "weekly_report_path": "reports/weekly/2026-W15.md",
  "promoted_config_path": null,
  "error": null,
  "details": [
    "Running replay...",
    "Replay complete: 42 events",
    "Building AI review packet...",
    "..."
  ]
}
```

### Governance Summary

```http
GET /api/v1/governance/summary
```

Get count summary of all parameter change requests by status.

**Response:**
```json
{
  "total": 5,
  "pending": 2,
  "approved": 2,
  "rejected": 1,
  "ready_to_promote": 2
}
```

### Symbol Catalog

```http
GET /api/v1/symbols
```

Returns symbol list for UI selector with governance counters per symbol.

Behavior:
- Default: reads from cached exchange catalog to reduce repeated Bybit fetch.
- If cache expired: refreshes from exchange adapter.
- If exchange fetch fails: reuses stale cache or falls back to replay dataset.

Optional query parameter:
- `refresh=true` to force refresh from exchange API (for newly listed coins).

**Response:**
```json
[
  {
    "symbol": "BTCUSDT",
    "total_requests": 3,
    "pending": 1,
    "approved": 1,
    "rejected": 1,
    "ready_to_promote": 1
  },
  {
    "symbol": "ETHUSDT",
    "total_requests": 0,
    "pending": 0,
    "approved": 0,
    "rejected": 0,
    "ready_to_promote": 0
  }
]
```

### Governance Live Stream

```http
GET /api/v1/governance/stream?symbol=BTCUSDT&interval_seconds=5
```

Stream status governance dan koneksi infra secara near real-time menggunakan Server-Sent Events (SSE).

Setiap event `governance` berisi payload seperti:

```json
{
  "symbol": "BTCUSDT",
  "summary": {
    "total": 5,
    "pending": 2,
    "approved": 2,
    "rejected": 1,
    "ready_to_promote": 2
  },
  "connections": {
    "postgres": {
      "enabled": true,
      "configured": true,
      "reachable": true,
      "detail": "ok"
    },
    "redis": {
      "enabled": false,
      "configured": true,
      "reachable": false,
      "detail": "disabled"
    },
    "exchange": {
      "provider": "bybit",
      "enabled": true,
      "configured": true,
      "reachable": true,
      "detail": "ok",
      "server_time": "1712921005"
    },
    "exchange_account": {
      "provider": "bybit",
      "enabled": true,
      "configured": false,
      "reachable": false,
      "detail": "missing ORACLE_EXCHANGE_API_KEY",
      "account_type": "UNIFIED"
    },
    "ai_analyst": {
      "provider": "gemini",
      "enabled": true,
      "configured": true,
      "reachable": true,
      "detail": "ok"
    }
  }
}
```

### Exchange Connectivity

```http
GET /api/v1/config/exchange
```

Returns exchange adapter connectivity status (Phase 8 baseline).

**Response:**
```json
{
  "provider": "bybit",
  "enabled": true,
  "configured": true,
  "reachable": true,
  "detail": "ok",
  "server_time": "1712921005"
}
```

### Exchange Account Connectivity

```http
GET /api/v1/config/exchange/account
```

Returns exchange private account preflight status (read-only auth check, no order placement).

**Response:**
```json
{
  "provider": "bybit",
  "enabled": true,
  "configured": true,
  "reachable": true,
  "detail": "ok",
  "account_type": "UNIFIED"
}
```

### AI Analyst Connectivity

```http
GET /api/v1/config/ai-analyst
```

Returns AI analyst adapter connectivity status.

**Response:**
```json
{
  "provider": "gemini",
  "enabled": true,
  "configured": true,
  "reachable": true,
  "detail": "ok"
}
```

For Gemini, recommended runtime env:

```bash
ORACLE_AI_PROVIDER=gemini
ORACLE_AI_ANALYST_BASE_URL=https://generativelanguage.googleapis.com
ORACLE_AI_ANALYST_HEALTH_PATH=/v1beta/models
ORACLE_ENABLE_AI_ANALYST_CONNECTIVITY=true
```

### List Governance Requests

```http
GET /api/v1/governance/requests
```

List all parameter change requests with their status and validation.

**Response:**
```json
[
  {
    "request_id": "req-001-uuid",
    "status": "pending",
    "is_valid": true,
    "promoted": false
  },
  {
    "request_id": "req-002-uuid",
    "status": "approved",
    "is_valid": true,
    "promoted": false
  }
]
```

### Approve Request

```http
POST /api/v1/governance/approve
```

Update the status of a parameter change request.

**Request Body:**
```json
{
  "request_id": "req-001-uuid",
  "status": "approved"
}
```

Valid statuses: `approved`, `rejected`, `pending`

**Response:**
```json
{
  "updated": true,
  "request_id": "req-001-uuid",
  "status": "approved"
}
```

### Promote Requests

```http
POST /api/v1/governance/promote
```

Promote all approved and valid requests to a strategy configuration file.

**Response (on success):**
```json
{
  "promoted": true,
  "config_path": "reports/strategy-configs/v1-abc123def456.json"
}
```

**Response (when no approved valid requests exist):**
```json
{
  "promoted": false,
  "reason": "no-approved-valid-requests"
}
```

## Integration with Scheduler

The API is designed to work with the weekly scheduler daemon. Schedule a weekly workflow:

```bash
cd src
PYTHONPATH=. python3 scheduler.py --start --day-of-week 0 --hour 8 --minute 0
```

This will automatically POST to `/api/v1/weekly-workflow` every Monday at 08:00.

Alternatively, for testing, trigger immediately:

```bash
cd src
PYTHONPATH=. python3 scheduler.py --run-now
```

## Error Handling

All endpoints return HTTP status codes and error details:

- `200 OK` - Successful operation
- `400 Bad Request` - Invalid request (e.g., invalid status value)
- `500 Internal Server Error` - Processing error (e.g., registry file not found)

Example error response:
```json
{
  "detail": "Failed to retrieve summary: No such file or directory"
}
```

## Environment Configuration

The API inherits configuration from environment variables:

- `PYTHONPATH` - Must include `src/` for imports
- `ORACLE_AI_PROVIDER` - AI provider name (default: `grok`)
- `ORACLE_RUNTIME_MODE` - Trading mode (default: `paper`)
- `ORACLE_EXCHANGE_ENV` - Exchange environment (default: `testnet`)

## Testing

Run API endpoint tests (requires FastAPI and dependencies installed):

```bash
cd /path/to/project-oracle
PYTHONPATH=src python3 -m unittest tests.test_api_endpoints -v
```

## Data Directories

The API expects the following directory structure:

```
project-oracle/
├── data/replay/
│   └── sample_snapshots.jsonl
├── registry/
│   └── parameter_change_requests.jsonl
├── reports/
│   ├── ai-review/
│   ├── weekly/
│   └── strategy-configs/
└── logs/
    └── weekly/
```

These are automatically created by the API if they don't exist.

## Next Steps

- Deploy to Railway or similar PaaS
- Add basic authentication (Bearer token or API key)
- Add request logging and monitoring
- Implement rate limiting
- Upgrade SSE stream to WebSocket channel if bidirectional event flow is needed
