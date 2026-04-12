from __future__ import annotations

import json
from typing import Any

from oracle.application.risk_controls import RiskState
from oracle.infrastructure.retry import with_retry


class RedisRiskRepository:
    def __init__(
        self,
        redis_url: str,
        key_prefix: str = "oracle:risk",
        ttl_seconds: int = 86400,
        max_retries: int = 2,
        retry_delay_seconds: float = 0.2,
    ) -> None:
        self._redis_url = redis_url
        self._key_prefix = key_prefix
        self._ttl_seconds = ttl_seconds
        self._max_retries = max_retries
        self._retry_delay_seconds = retry_delay_seconds

    def save_state(self, state: RiskState) -> None:
        key = f"{self._key_prefix}:state"

        def operation() -> None:
            client = self._build_client()
            client.setex(key, self._ttl_seconds, json.dumps(state.__dict__, ensure_ascii=True))

        try:
            with_retry(
                operation,
                max_retries=self._max_retries,
                delay_seconds=self._retry_delay_seconds,
            )
        except Exception:
            # Keep runtime safe: risk state can be recomputed from defaults if Redis is unavailable.
            return

    def load_state(self) -> RiskState:
        key = f"{self._key_prefix}:state"

        def operation() -> RiskState:
            client = self._build_client()
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

        try:
            return with_retry(
                operation,
                max_retries=self._max_retries,
                delay_seconds=self._retry_delay_seconds,
            )
        except Exception:
            return RiskState()

    def _build_client(self):
        try:
            import redis  # type: ignore
        except ImportError as exc:
            raise RuntimeError("redis package is required for RedisRiskRepository") from exc
        return redis.from_url(self._redis_url, decode_responses=True)
