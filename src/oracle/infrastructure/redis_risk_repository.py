from __future__ import annotations

import json
from typing import Any

from oracle.application.risk_controls import RiskState


class RedisRiskRepository:
    def __init__(self, redis_url: str, key_prefix: str = "oracle:risk") -> None:
        self._redis_url = redis_url
        self._key_prefix = key_prefix

    def save_state(self, state: RiskState) -> None:
        client = self._build_client()
        key = f"{self._key_prefix}:state"
        client.set(key, json.dumps(state.__dict__))

    def load_state(self) -> RiskState:
        client = self._build_client()
        key = f"{self._key_prefix}:state"
        raw = client.get(key)
        if not raw:
            return RiskState()

        decoded: dict[str, Any] = json.loads(raw)
        return RiskState(
            cumulative_loss_r=float(decoded.get("cumulative_loss_r", 0.0)),
            consecutive_losses=int(decoded.get("consecutive_losses", 0)),
            is_locked=bool(decoded.get("is_locked", False)),
            lock_reason=str(decoded.get("lock_reason", "")),
        )

    def _build_client(self):
        try:
            import redis  # type: ignore
        except ImportError as exc:
            raise RuntimeError("redis package is required for RedisRiskRepository") from exc
        return redis.from_url(self._redis_url, decode_responses=True)
