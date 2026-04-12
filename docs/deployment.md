# Project Oracle Deployment Guide

## Prerequisites

- Python 3.12+
- Git
- Northflank account (untuk cloud deployment) atau Linux VPS
- Optional: PostgreSQL, Redis

## Google Cloud Trial Deployment (Recommended for Current Phase)

Gunakan ini jika fokus utama adalah deploy cepat selama masa trial credit tanpa refactor arsitektur storage.

Kenapa cocok untuk saat ini:
- arsitektur saat ini masih file-based (`registry`, `reports`, `runtime-fallback`)
- VM menjaga filesystem persisten sederhana
- biaya tetap rendah dengan `e2-micro` di region US

### Step 1: Siapkan GCP CLI lokal

Pastikan `gcloud` sudah login:

```bash
gcloud auth login
gcloud auth application-default login
```

### Step 2: Buat VM dan auto-bootstrap

Dari root repository:

```bash
chmod +x scripts/gcp/create_vm.sh scripts/gcp/bootstrap_vm.sh
./scripts/gcp/create_vm.sh <PROJECT_ID> us-central1-a project-oracle-vm
```

Script ini akan:
- membuat VM Debian (`e2-micro`, disk 20GB)
- membuka firewall port `8000`
- clone repository ke `/opt/project-oracle`
- install dependencies dari `requirements.txt`
- pasang service `oracle-api` dan `oracle-scheduler`

### Step 3: Ambil public IP dan verifikasi

```bash
gcloud compute instances describe project-oracle-vm --zone=us-central1-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

Lalu test endpoint:

```bash
curl http://<PUBLIC_IP>:8000/health
curl -X POST http://<PUBLIC_IP>:8000/api/v1/weekly-workflow
```

### Step 4: Monitoring service

```bash
gcloud compute ssh project-oracle-vm --zone=us-central1-a --command="sudo systemctl status oracle-api oracle-scheduler"
```

### Cost baseline (trial-friendly)

- machine type: `e2-micro`
- disk: `pd-standard` 20GB
- region: `us-central1`

Upgrade hanya jika benar-benar perlu (memory pressure, response lambat, atau persistence eksternal aktif).

## Local Development Setup

### 1. Clone and Install

```bash
git clone https://github.com/fatidaprilian/project-oracle.git
cd project-oracle

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install project dependencies
pip install apscheduler fastapi uvicorn
```

### 2. Configure Environment

Copy and edit .env.example:

```bash
cp .env.example .env
```

Recommended for local + production baseline:
```
ORACLE_FRONTEND_URL=http://localhost:3000
ORACLE_ALLOWED_ORIGINS=http://localhost:3000
ORACLE_API_AUTH_ENABLED=true
ORACLE_API_AUTH_TOKEN=
ORACLE_AUTH_POSTGRES_DSN=postgresql://<user>:<pass>@<host>:5432/<db>
ORACLE_AUTH_HASH_ITERATIONS=390000
```

Setelah env auth siap, buat akun dashboard pertama (tanpa register UI):

```bash
PYTHONPATH=src python3 scripts/security/create_auth_user.py --username <USERNAME> --role admin
```

Password akan diminta via prompt dan disimpan sebagai hash di tabel `auth_users`.

Required variables:
```
ORACLE_RUNTIME_MODE=paper
ORACLE_EXCHANGE_ENV=testnet
ORACLE_AI_PROVIDER=grok
```

Optional (for production):
```
ORACLE_ENABLE_POSTGRES=true
ORACLE_POSTGRES_DSN=postgresql://user:pass@localhost:5432/oracle
ORACLE_ENABLE_REDIS=true
ORACLE_REDIS_URL=redis://localhost:6379/0
```

Optional (for external AI/sentiment integrations):
```
ORACLE_SENTIMENT_BASE_URL=https://<sentiment-provider>
ORACLE_SENTIMENT_API_KEY=<your-sentiment-key>
ORACLE_AI_ANALYST_BASE_URL=https://<ai-analyst-provider>
ORACLE_AI_ANALYST_API_KEY=<your-ai-analyst-key>
ORACLE_ENABLE_AI_ANALYST_CONNECTIVITY=true
ORACLE_AI_ANALYST_HEALTH_PATH=/health
```

Optional (for exchange connectivity checks):
```
ORACLE_ENABLE_EXCHANGE_CONNECTIVITY=true
ORACLE_EXCHANGE_PROVIDER=bybit
ORACLE_EXCHANGE_BASE_URL=https://api-testnet.bybit.com
ORACLE_EXCHANGE_TIMEOUT_SECONDS=3.0
```

### 3. Run Tests

```bash
PYTHONPATH=src python3 -m unittest discover tests -v
```

Expected: 35+ tests passing

### 4. Test API Locally

Start the API server:

```bash
cd src
PYTHONPATH=. python3 run_api.py --reload
```

In another terminal, test endpoints:

```bash
# Health check
curl http://localhost:8000/health

# Root endpoint (contains docs and optional frontend URL)
curl http://localhost:8000/

# Production readiness flags for env variables
curl http://localhost:8000/api/v1/config/readiness

# Trigger weekly workflow
curl -X POST http://localhost:8000/api/v1/weekly-workflow

# Get governance summary
curl http://localhost:8000/api/v1/governance/summary

# List requests
curl http://localhost:8000/api/v1/governance/requests

# AI analyst connectivity
curl http://localhost:8000/api/v1/config/ai-analyst
```

### 5. Test Scheduler Locally

Run workflow immediately (for testing):

```bash
cd src
PYTHONPATH=. python3 scheduler.py --run-now
```

Schedule for weekly execution (Monday 08:00):

```bash
cd src
PYTHONPATH=. python3 scheduler.py --start --day-of-week 0 --hour 8
```

## Northflank Deployment

### Step 1: Create Northflank Project

1. Go to https://northflank.com
2. Create new project
3. Connect GitHub repository
4. Select `project-oracle` repo

### Step 2: Add Environment Variables

In Northflank dashboard, set environment variables:

```
PYTHONPATH=src
ORACLE_RUNTIME_MODE=paper
ORACLE_EXCHANGE_ENV=testnet
ORACLE_AI_PROVIDER=grok
ORACLE_ENABLE_POSTGRES=false  # until Phase 7
```

Optional: Add PostgreSQL/Redis plugins via Northflank dashboard

### Step 3: Configure Services

Create two services from the same repository and Dockerfile:

Web service:
- Build from `Dockerfile`
- Start command: `python3 run_api.py --host 0.0.0.0`
- Port: use `PORT` from environment or Northflank default port mapping

Worker service:
- Build from the same `Dockerfile`
- Start command: `python3 scheduler.py --start --day-of-week 0 --hour 8`

Use a US region for now. That is sufficient for the current paper-trading scope and keeps latency predictable.

### Step 4: Deploy

Push to GitHub:

```bash
git add .
git commit -m "deploy: configure for Railway"
git push origin main
```

Northflank auto-deploys on push.

### Step 5: Verify Deployment

Once deployed, Northflank shows your URL (example format depends on the service name):

```bash
# Health check
curl https://<your-service-url>/health

# Trigger workflow
curl -X POST https://<your-service-url>/api/v1/weekly-workflow
```

Check logs in Northflank dashboard.

### Dockerfile

Northflank can build directly from the repository using the Dockerfile at the project root. The API service uses the same image as the scheduler service, so the runtime logic stays identical and only the command differs.

If you want to keep Railway support as a fallback, the same Dockerfile can be reused there too.

## Railway Deployment (Fallback)

The Railway path still works as a fallback if you want a second platform option later. Keep the same environment variables and use the same Dockerfile-based build.

## Frontend Deployment (Vercel)

Frontend boundary lives in `web/` and is intended to deploy separately to Vercel.

Recommended env values for the frontend:

```bash
VITE_API_URL=https://project-oracle-133425616833.asia-southeast2.run.app
VITE_API_TOKEN=
```

If backend auth is enabled later, set `VITE_API_TOKEN` to the same bearer token you store in backend secrets.

The Vercel project can point to the `web/` folder as the root directory, then run:

```bash
npm install
npm run build
```

Deploy output will be the frontend root, while the API remains on Cloud Run.

## Frontend Access

Current Cloud Run URL below is API service, not frontend app shell:

```
https://project-oracle-133425616833.asia-southeast2.run.app/
```

Use these URLs for API service:

```bash
# API health
curl https://project-oracle-133425616833.asia-southeast2.run.app/health

# API docs (Swagger)
https://project-oracle-133425616833.asia-southeast2.run.app/docs
```

For frontend app access in local development:

```bash
cd web
cp .env.example .env
npm run dev -- --host 0.0.0.0 --port 3000
```

Then open:

```
http://localhost:3000
```

Set `VITE_API_URL` in `web/.env` to point to local API or Cloud Run API.

## VPS Deployment (Linux)

### 1. Server Setup

```bash
# SSH to VPS
ssh user@your-vps.com

# Install Python 3.12
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv git

# Clone repo
git clone https://github.com/fatidaprilian/project-oracle.git
cd project-oracle

# Setup venv
python3.12 -m venv .venv
source .venv/bin/activate
pip install apscheduler fastapi uvicorn
```

### 2. Systemd Services

Create `/etc/systemd/system/oracle-api.service`:

```ini
[Unit]
Description=Project Oracle API
After=network.target

[Service]
User=appuser
WorkingDirectory=/home/appuser/project-oracle
Environment="PYTHONPATH=/home/appuser/project-oracle/src"
ExecStart=/home/appuser/project-oracle/.venv/bin/python3 run_api.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/oracle-scheduler.service`:

```ini
[Unit]
Description=Project Oracle Scheduler
After=network.target

[Service]
User=appuser
WorkingDirectory=/home/appuser/project-oracle
Environment="PYTHONPATH=/home/appuser/project-oracle/src"
ExecStart=/home/appuser/project-oracle/.venv/bin/python3 scheduler.py --start
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 3. Start Services

```bash
sudo systemctl enable oracle-api.service
sudo systemctl start oracle-api.service

sudo systemctl enable oracle-scheduler.service
sudo systemctl start oracle-scheduler.service

# Check status
sudo systemctl status oracle-api.service
sudo systemctl status oracle-scheduler.service
```

### 4. Reverse Proxy (Nginx)

Configure `/etc/nginx/sites-available/oracle`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart:

```bash
sudo ln -s /etc/nginx/sites-available/oracle /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

## Monitoring

### API Logs

Railway: View in dashboard under "Logs"

VPS:
```bash
journalctl -u oracle-api.service -f
journalctl -u oracle-scheduler.service -f
```

### Weekly Workflow Logs

```bash
tail -f logs/weekly/scheduler-*.log
tail -f logs/weekly/workflow-*.json | jq .
```

### Health Endpoint

Monitor via cron job:

```bash
# /usr/local/bin/check-oracle-health.sh
#!/bin/bash
STATUS=$(curl -s http://localhost:8000/health | jq -r '.status')
if [ "$STATUS" != "healthy" ]; then
    echo "Oracle API unhealthy" | mail -s "Alert" ops@example.com
fi
```

Add to crontab:

```bash
*/5 * * * * /usr/local/bin/check-oracle-health.sh
```

### One-Command Production Smoke Check

Gunakan script ini setiap selesai deploy Cloud Run untuk verifikasi cepat endpoint utama:

```bash
./scripts/ops/check_prod.sh
```

Opsional jika ingin cek URL lain:

```bash
./scripts/ops/check_prod.sh https://your-service-url.run.app
```

Script ini memverifikasi:
- `/health`
- `/api/v1/config/readiness`
- `/api/v1/config/connections`
- `/docs`

Script akan exit code `1` jika ada dependency yang enabled tapi tidak reachable.

## Troubleshooting

### API won't start

Check logs for import errors:
```bash
cd src && python3 -c "from api.main import app; print('OK')"
```

### Scheduler not running workflows

Check cron/systemd logs:
```bash
sudo journalctl -u oracle-scheduler.service -n 50
```

Verify schedule format:
```bash
cd src && python3 scheduler.py --run-now
```

### Weekly reports not being created

Check dataset exists:
```bash
wc -l data/replay/sample_snapshots.jsonl
```

Check governance registry permissions:
```bash
ls -la registry/
```

## Rollback

If deployment fails:

```bash
git revert <commit-hash>
git push origin main
```

Railway auto-redeploys on push (should take 2-5 minutes).

## Next Steps (Phase 7+)

- Add Basic Auth middleware to API
- Database persistence (PostgreSQL migration)
- Real-time dashboard (WebSocket support)
- Multi-symbol portfolio mode
- Email alerts for governance decisions
- Frontend React app deployment
