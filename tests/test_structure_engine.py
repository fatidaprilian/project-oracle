from __future__ import annotations

import unittest

from oracle.domain.models import MarketRegime, MarketSnapshot
from oracle.modules.structure_engine import evaluate_structure


class StructureEngineTest(unittest.TestCase):
    def test_should_detect_uptrend_when_closes_are_ascending(self) -> None:
        snapshot = MarketSnapshot(
            symbol="BTCUSDT",
            timeframe="15m",
            closes=[100.0, 101.0, 102.0],
            highs=[101.0, 102.0, 103.0],
            lows=[99.0, 100.0, 101.0],
            current_price=102.0,
            volume=1000.0,
        )

        signal = evaluate_structure(snapshot)

        self.assertEqual(signal.market_regime, MarketRegime.UPTREND)
        self.assertTrue(signal.is_tradeable)


if __name__ == "__main__":
    unittest.main()
