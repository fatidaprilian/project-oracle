from __future__ import annotations

import unittest

from oracle.domain.models import MarketSnapshot
from oracle.modules.pullback_strategy import evaluate_stock_pullback


def _build_snapshot(current_volume: float, silent_pullback: bool) -> MarketSnapshot:
    closes = [100.0 + (i * 0.25) for i in range(120)]
    closes.extend([148.0 + (i * 0.02) for i in range(98)])
    closes.extend([149.4, 150.3])

    highs = [close + 0.35 for close in closes]
    lows = [close - 0.45 for close in closes]

    highs[-2] = 149.8
    lows[-2] = 148.7
    highs[-1] = 150.6
    lows[-1] = 147.2

    volumes = [1000.0 for _ in closes]
    if silent_pullback:
        volumes[-6:-1] = [700.0, 680.0, 640.0, 620.0, 600.0]
    else:
        volumes[-6:-1] = [1000.0, 1000.0, 1000.0, 1000.0, 1000.0]
    volumes[-1] = current_volume

    return MarketSnapshot(
        symbol="AAPL",
        timeframe="1h",
        closes=closes,
        highs=highs,
        lows=lows,
        current_price=closes[-1],
        volume=current_volume,
        volumes=volumes,
    )


class PullbackStrategyTest(unittest.TestCase):
    def test_should_prioritize_silent_pullback_when_all_filters_align(self) -> None:
        snapshot = _build_snapshot(current_volume=1500.0, silent_pullback=True)

        signal = evaluate_stock_pullback(snapshot)

        self.assertTrue(signal.is_valid)
        self.assertEqual(signal.strategy_name, "SILENT_PULLBACK")
        self.assertGreaterEqual(signal.volume_ratio, 1.2)

    def test_should_fallback_to_golden_pullback_when_not_silent(self) -> None:
        snapshot = _build_snapshot(current_volume=1300.0, silent_pullback=False)

        signal = evaluate_stock_pullback(snapshot)

        self.assertTrue(signal.is_valid)
        self.assertEqual(signal.strategy_name, "GOLDEN_PULLBACK")

    def test_should_reject_when_volume_anomaly_is_missing(self) -> None:
        snapshot = _build_snapshot(current_volume=1000.0, silent_pullback=False)

        signal = evaluate_stock_pullback(snapshot)

        self.assertFalse(signal.is_valid)
        self.assertIn("VOLUME_BELOW_1P2_MA20", signal.reason_codes)


if __name__ == "__main__":
    unittest.main()
