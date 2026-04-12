# Worker Service

This folder is the deployment entrypoint for background jobs and weekly orchestration.

Runtime:
- implementation lives in `src/scheduler.py`
- workflow logic lives in `src/oracle/application/`
- local/service startup can use `services/worker/entrypoint.py`

Example:
```bash
PYTHONPATH=src python services/worker/entrypoint.py --start
```
