# Services

Service boundaries for Project Oracle:

- `api/` - HTTP API and governance surface
- `worker/` - scheduled weekly workflow and background jobs

The actual application logic remains in `src/` for now, while these folders act as service entrypoints and deployment boundaries.
