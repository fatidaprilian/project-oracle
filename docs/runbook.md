# Project Oracle Operations Runbook

## Overview

This runbook covers operational tasks for running Project Oracle in production.

## Weekly Operations Workflow

### Automated (Scheduler) Mode

The scheduler can automatically run the weekly workflow on a schedule:

```bash
cd src
PYTHONPATH=. python3 scheduler.py --start --day-of-week 0 --hour 8
```

This will run every Monday at 08:00. Logs are written to `logs/weekly/scheduler-*.log`.

### Manual Workflow Trigger

If using the API:

```bash
curl -X POST http://localhost:8000/api/v1/weekly-workflow
```

Or via CLI:

```bash
cd src
PYTHONPATH=. python3 weekly_report.py
```

### Workflow Steps

The `weekly_workflow.py` orchestrator automatically:

1. Runs replay on historical snapshot data
2. Generates AI review packet with worst trades
3. Records parameter change request (status: pending)
4. Generates weekly report with governance summary
5. Attempts to promote approved valid requests to strategy config

Duration: ~5-10 seconds for sample dataset.

## Governance Operations

### List Parameter Change Requests

```bash
cd src
PYTHONPATH=. python3 strategy_governance.py list
```

Or via API:

```bash
curl http://localhost:8000/api/v1/governance/requests
```

### Approve a Change Request

```bash
cd src
PYTHONPATH=. python3 strategy_governance.py set-status --request-id <ID> --status approved
```

Or via API:

```bash
curl -X POST http://localhost:8000/api/v1/governance/approve \
  -H "Content-Type: application/json" \
  -d '{"request_id":"<ID>","status":"approved"}'
```

### Reject a Change Request

```bash
cd src
PYTHONPATH=. python3 strategy_governance.py set-status --request-id <ID> --status rejected
```

### Promote Approved Requests

```bash
cd src
PYTHONPATH=. python3 strategy_governance.py promote
```

Or via API:

```bash
curl -X POST http://localhost:8000/api/v1/governance/promote
```

This checks for all `approved` and `is_valid=true` requests and merges their parameters into a strategy config JSON file under `reports/strategy-configs/`.

## Monitoring

### API Health Check

```bash
curl http://localhost:8000/health
```

Should return `{"status":"healthy","version":"0.1.0"}`.

### Weekly Logs

Check execution logs:

```bash
tail -f logs/weekly/scheduler-*.log
```

### Weekly Reports

View latest generated report:

```bash
cat reports/weekly/2026-W15.md
```

View latest AI review packet:

```bash
cat reports/ai-review/2026-W15-ai-review.json
```

View governance registry:

```bash
tail registry/parameter_change_requests.jsonl | jq .
```

## Incident Response

### API Service Down

1. Check if process is still running: `pgrep -f "python.*run_api.py"`
2. Check logs: `tail -50 logs/api.log` (if logging configured)
3. Restart: `cd src && PYTHONPATH=. python3 run_api.py`

### Scheduler Not Running Weekly Workflows

1. Verify scheduler process: `pgrep -f "python.*scheduler.py"`
2. Check scheduler logs: `tail -f logs/weekly/scheduler-*.log`
3. Restart scheduler: `cd src && PYTHONPATH=. python3 scheduler.py --start`

### Replay Failure

1. Check dataset file exists: `ls -la data/replay/sample_snapshots.jsonl`
2. Verify file format (JSONL): `head -1 data/replay/sample_snapshots.jsonl`
3. Check error in workflow result JSON under logs/

### Registry Corruption

Backup and inspect:

```bash
cp registry/parameter_change_requests.jsonl registry/parameter_change_requests.jsonl.bak
jq . registry/parameter_change_requests.jsonl | less
```

### Full System Recovery

1. Stop services: `pkill -f "python.*run_api.py" && pkill -f "python.*scheduler.py"`
2. Backup state: `cp -r registry reports logs backup-$(date +%Y%m%d)/`
3. Clear temporary files: `rm -rf reports/ai-review/* reports/strategy-configs/*` (optional)
4. Restart API: `cd src && PYTHONPATH=. python3 run_api.py &`
5. Restart scheduler: `cd src && PYTHONPATH=. python3 scheduler.py --start &`

## Deployment Checklist

Before going live:

- [ ] Environment variables configured (`.env` or exported)
- [ ] Data directories exist: `data/replay/`, `registry/`, `reports/`, `logs/`
- [ ] Sample dataset present: `data/replay/sample_snapshots.jsonl`
- [ ] PostgreSQL/Redis adapters configured (optional)
- [ ] API server tested: `curl http://localhost:8000/health`
- [ ] Scheduler tested: `python3 scheduler.py --run-now`
- [ ] Weekly report generated successfully
- [ ] Logs directory has write permissions

## Regular Maintenance

### Daily

- Monitor health check endpoint
- Review error logs from overnight runs

### Weekly (or on-demand)

- Analyze weekly report for strategy quality
- Review parameter change requests and approve/reject
- Promote approved changes to strategy config
- Test replay with latest market data

### Monthly

- Archive old logs: `mv logs/weekly/* logs/archive/`
- Review historical config promotions
- Validate database constraints (if using PostgreSQL)

## Performance Notes

- First replay on a cold dataset (~1MB typical): 10-20 seconds
- Subsequent replays (cached): 2-5 seconds
- Workflow orchestration (all steps): 15-30 seconds
- API response time (excluding workflow): <100ms
- Scheduler overhead: <1% CPU when idle

## Backward Compatibility

Current version is 0.1.0 (Alpha).

- API is not versioned below `/api/v1/`
- Registry JSONL format may change; always backup before upgrade
- Strategy config JSON format stable

## Next Steps

Phase 7 (Future):

- Database persistence (PostgreSQL)
- Real-time monitoring dashboard
- WebSocket live status updates
- Parameter runtime loading (dynamic config hot-reload)
- Multi-symbol support
