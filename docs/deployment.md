# Project Oracle Deployment Guide

## Prerequisites

- Python 3.12+
- Git
- Railway account (untuk cloud deployment) atau Linux VPS
- Optional: PostgreSQL, Redis

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

# Trigger weekly workflow
curl -X POST http://localhost:8000/api/v1/weekly-workflow

# Get governance summary
curl http://localhost:8000/api/v1/governance/summary

# List requests
curl http://localhost:8000/api/v1/governance/requests
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

## Railway Deployment

### Step 1: Create Railway Project

1. Go to https://railway.app
2. Create new project
3. Connect GitHub repository
4. Select `project-oracle` repo

### Step 2: Add Environment Variables

In Railway dashboard, set environment variables:

```
PYTHONPATH=src
ORACLE_RUNTIME_MODE=paper
ORACLE_EXCHANGE_ENV=testnet
ORACLE_AI_PROVIDER=grok
ORACLE_ENABLE_POSTGRES=false  # until Phase 7
```

Optional: Add PostgreSQL/Redis plugins via Railway dashboard

### Step 3: Configure Start Command

Railway should auto-detect Python. If not, create `Procfile`:

```
web: cd src && python3 run_api.py --host 0.0.0.0 --port $PORT
scheduler: cd src && python3 scheduler.py --start --day-of-week 0 --hour 8
```

Or configure in Railway dashboard:
- **Web Service**: `src/run_api.py`
- **Worker Service**: `src/scheduler.py --start`

### Step 4: Deploy

Push to GitHub:

```bash
git add .
git commit -m "deploy: configure for Railway"
git push origin main
```

Railway auto-deploys on push.

### Step 5: Verify Deployment

Once deployed, Railway shows your URL (e.g., `https://project-oracle-prod.up.railway.app`):

```bash
# Health check
curl https://project-oracle-prod.up.railway.app/health

# Trigger workflow
curl -X POST https://project-oracle-prod.up.railway.app/api/v1/weekly-workflow
```

Check logs in Railway dashboard.

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
