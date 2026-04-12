from __future__ import annotations

import unittest

from oracle.application.risk_controls import RiskState
from oracle.infrastructure.redis_risk_repository import RedisRiskRepository


class _FakeRedisClient:
    def __init__(self) -> None:
        self.saved: dict[str, tuple[int, str]] = {}

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        self.saved[key] = (ttl_seconds, value)

    def get(self, key: str) -> str | None:
        item = self.saved.get(key)
        if not item:
            return None
        return item[1]


class RedisRiskRepositoryTest(unittest.TestCase):
    def test_should_store_state_with_ttl_policy(self) -> None:
        repository = RedisRiskRepository(
            redis_url="redis://unused",
            ttl_seconds=123,
            max_retries=0,
            retry_delay_seconds=0.0,
        )
        fake_client = _FakeRedisClient()
        repository._build_client = lambda: fake_client  # type: ignore[method-assign]

        repository.save_state(RiskState(cumulative_loss_r=2.5, consecutive_losses=1))

        ttl, _ = fake_client.saved["oracle:risk:state"]
        self.assertEqual(ttl, 123)

    def test_should_return_default_state_when_load_fails(self) -> None:
        repository = RedisRiskRepository(
            redis_url="redis://unused",
            max_retries=0,
            retry_delay_seconds=0.0,
        )
        repository._build_client = lambda: (_ for _ in ()).throw(RuntimeError("down"))  # type: ignore[method-assign]

        state = repository.load_state()

        self.assertEqual(state.cumulative_loss_r, 0.0)
        self.assertFalse(state.is_locked)


if __name__ == "__main__":
    unittest.main()
