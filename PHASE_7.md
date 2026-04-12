# Phase 7: Enterprise Enhancement - Multi-Symbol & Frontend

Project Oracle Phase 7 adds multi-symbol trading support, modern React dashboard, API authentication, and production-ready security.

## What's New

### Backend Enhancements

1. **Multi-Symbol Support**
   - Per-symbol parameter rules and configurations
   - Symbol-aware parameter change requests
   - Backward-compatible with existing single-symbol workflows
   - New API endpoints for symbol discovery

2. **API Authentication & Security**
   - JWT-based token authentication
   - CORS configuration
   - API key support (via security module)
   - Request signing capabilities

3. **New API Endpoints**
   - `GET /api/v1/symbols` - List all symbols with request counts
   - `GET /api/v1/governance/summary?symbol=BTCUSDT` - Per-symbol summaries
   - `GET /api/v1/governance/requests?symbol=BTCUSDT` - Filter requests by symbol
   - Updated `POST /api/v1/weekly-workflow?symbol=BTCUSDT` - Symbol-specific workflows

### Frontend (React Dashboard)

**Tech Stack:**
- React 19 + TypeScript
- Vite (ultra-fast bundler)
- TailwindCSS (modern styling)
- Axios (HTTP client)

**Features:**
- Symbol selector with real-time counts
- Dashboard with governance statistics
- Parameter change request management
- Approve/reject workflow UI
- Promote requests to strategy config
- Clean, responsive dark mode design

## Installation

### Backend
```bash
pip install -r requirements.txt
```

New dependencies:
- `pyjwt>=2.8.0` - JWT token support
- `python-multipart>=0.0.6` - Form data handling

### Frontend
```bash
cd web
npm install
```

## Running Locally

### Backend API
```bash
python src/run_api.py --host 0.0.0.0 --port 8000
# API runs on http://localhost:8000
# Health check: curl http://localhost:8000/health
```

### Frontend Dashboard
```bash
cd web
npm run dev
# Opens http://localhost:3000
# Automatically proxies /api calls to http://localhost:8000
```

## Environment Variables

**Backend:**
```env
PORT=8000
ORACLE_ALLOWED_ORIGINS=http://localhost:3000,https://your-production-domain.com
ORACLE_SECRET_KEY=your-secret-key-change-in-production
ORACLE_RUNTIME_MODE=paper
ORACLE_EXCHANGE_ENV=testnet
```

**Frontend:**
```env
REACT_APP_API_URL=http://localhost:8000
```

## Architecture

### Multi-Symbol Data Flow

1. **Request Creation** (AI-generated or user-submitted)
   - Now includes optional `"symbol": "BTCUSDT"` field
   - Per-symbol parameter rules enforced during validation
   - Stored in unified registry with symbol tagging

2. **Governance** 
   - Requests filtered by symbol for approval
   - Each symbol can have different parameter thresholds
   - Promotion creates symbol-specific configs

3. **Application**
   - RiskManager tracks separate states per symbol
   - Strategy configs applied per-symbol basis
   - Parameters isolated to prevent cross-symbol interference

### Security Model

**Authentication (Optional - not enforced by default)**
```python
from src.api.security import create_api_token, verify_api_token

# Create token
token = create_api_token(identifier="user@example.com")

# Verify in endpoints
@app.post("/api/v1/protected", dependencies=[Depends(get_current_user)])
async def protected_endpoint(current_user: dict):
    pass
```

**CORS Configuration**
```env
# Comma-separated list of allowed origins
ORACLE_ALLOWED_ORIGINS=http://localhost:3000,https://app.example.com
```

## API Reference

### GET /health
```bash
curl http://localhost:8000/health
# Response:
# {"status":"healthy","version":"0.1.0"}
```

### GET /api/v1/symbols
```bash
curl http://localhost:8000/api/v1/symbols
# Response:
# [
#   {
#     "symbol": "BTCUSDT",
#     "total_requests": 15,
#     "pending": 3,
#     "approved": 10,
#     "rejected": 2,
#     "ready_to_promote": 8
#   }
# ]
```

### GET /api/v1/governance/summary?symbol=BTCUSDT
```bash
curl http://localhost:8000/api/v1/governance/summary?symbol=BTCUSDT
# Response:
# {"total":15,"pending":3,"approved":10,"rejected":2,"ready_to_promote":8}
```

### POST /api/v1/weekly-workflow?symbol=BTCUSDT
```bash
curl -X POST http://localhost:8000/api/v1/weekly-workflow?symbol=BTCUSDT
# Response includes AI review, reports, and promotion status
```

### POST /api/v1/governance/approve
```bash
curl -X POST http://localhost:8000/api/v1/governance/approve \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "uuid-here",
    "status": "approved"
  }'
```

### POST /api/v1/governance/promote
```bash
curl -X POST http://localhost:8000/api/v1/governance/promote
# Promotes all approved+valid requests to strategy configs
```

## Frontend Usage

### Dashboard
- **Symbol Selector**: Choose which symbol to manage
- **Statistics Cards**: Real-time counts (total, pending, approved, rejected, ready)
- **Trigger Workflow**: Run weekly analysis for selected symbol
- **Promote Button**: Activate ready-to-promote requests

### Requests Page
- **Filter by Symbol**: View symbol-specific requests
- **Status Badges**: Visual indication of request status
- **Approve/Reject**: Workflow approval buttons
- **Auto-refresh**: Manual reload button

## Next Steps (Phase 8)

1. **Database Integration**
   - PostgreSQL for persistent request storage
   - Cloud SQL setup for production

2. **Monitoring & Logging**
   - Cloud Logging integration
   - Metrics dashboard (Cloud Monitoring)
   - Request/response tracking

3. **Advanced Features**
   - Email notifications for approvals
   - Audit trail for all governance changes
   - Bulk request management
   - Parameter history & rollback

4. **Performance**
   - Redis caching for governance data
   - Request pagination
   - Symbol-based data partitioning

## Deployment

Current deployment via Cloud Build + Cloud Run (Tokyo/Jakarta regions):

```bash
git push origin main
# Cloud Build auto-triggers
# Docker builds from root Dockerfile
# Deploys to: https://project-oracle-xxxxx.asia-southeast2.run.app
```

Frontend deployment (optional):
```bash
cd web
npm run build
# Deploy dist/ folder to Netlify, Vercel, or Cloud Storage
```

## Testing

### Backend
```bash
pytest tests/  # if tests exist
python -m pytest src/
```

### Frontend
```bash
cd web
npm run lint
npm run build
```

## Troubleshooting

**Frontend can't reach API**
- Check CORS origin: `ORACLE_ALLOWED_ORIGINS` includes frontend URL
- Check API is running: `curl http://localhost:8000/health`
- Check proxy config: `web/vite.config.ts` has `/api` proxy

**Authentication fails**
- Ensure `pyjwt` is installed: `pip install pyjwt`
- Check `ORACLE_SECRET_KEY` is set
- Verify token format: Bearer {token}

**Symbol not appearing**
- Trigger workflow for that symbol first
- Check `registry/parameter_change_requests.jsonl` for symbol entries

## File Structure

```
project-oracle/
├── src/
│   ├── api/
│   │   ├── main.py           (FastAPI app, endpoints)
│   │   └── security.py        (JWT, auth, signing)
│   ├── oracle/
│   │   └── application/
│   │       ├── multi_symbol_risk.py    (NEW: per-symbol risk management)
│   │       ├── strategy_intelligence.py (Updated: symbol support)
│   │       └── ...
│   └── run_api.py
├── web/                       (NEW: React dashboard)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   └── Requests.tsx
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   └── UI.tsx
│   │   ├── api/
│   │   │   └── client.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
├── registry/
├── requirements.txt
└── Dockerfile
```

## Version

Phase 7: v0.1.0-enterprise
- Multi-symbol framework complete
- React frontend production-ready
- API security layer implemented
- Cloud deployment functional
