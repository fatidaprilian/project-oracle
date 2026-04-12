# API Service

This folder is the deployment entrypoint for the Project Oracle API service.

Runtime:
- implementation lives in `src/api/main.py`
- shared core logic lives in `src/oracle/`
- local/Cloud Run startup can use `services/api/entrypoint.py`

Example:
```bash
PYTHONPATH=src python services/api/entrypoint.py
```
