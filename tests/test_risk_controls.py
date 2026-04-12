from __future__ import annotations

import unittest

from oracle.application.risk_controls import RiskConfig, RiskGuard
from oracle.domain.models import MarketSnapshot


class RiskControlsTest(unittest.TestCase):
    def test_should_reject_trade_when_volume_below_threshold(self) -> None:
        guard = RiskGuard(RiskConfig(min_volume_threshold=1000.0))
        snapshot = MarketSnapshot(
            symbol="BTCUSDT",
            timeframe="15m",
            closes=[100.0, 101.0, 102.0],
            highs=[100.5, 101.5, 102.5],
            lows=[99.5, 100.5, 101.5],
            current_price=102.0,
            volume=500.0,
        )

        is_allowed, reason = guard.pre_trade_check(snapshot)

        self.assertFalse(is_allowed)
        self.assertEqual(reason, "LOW_LIQUIDITY")

    def test_should_lock_guard_when_consecutive_losses_reach_limit(self) -> None:
        guard = RiskGuard(RiskConfig(max_consecutive_losses=2))

        guard.register_closed_trade(-1.0)
        guard.register_closed_trade(-0.5)

        self.assertTrue(guard.state.is_locked)
        self.assertEqual(guard.state.lock_reason, "CONSECUTIVE_LOSS_LIMIT")


if __name__ == "__main__":
    unittest.main()
