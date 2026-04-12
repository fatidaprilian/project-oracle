from __future__ import annotations

import os

import uvicorn

from api.main import app


def main() -> int:
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
