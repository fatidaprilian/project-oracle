from __future__ import annotations

import unittest

from oracle.domain.models import MarketSnapshot, ZoneSignal, ZoneType
from oracle.modules.confluence_engine import evaluate_confluence


class ConfluenceEngineTest(unittest.TestCase):
    def test_should_mark_valid_when_price_near_cluster(self) -> None:
        snapshot = MarketSnapshot(
            symbol="BTCUSDT",
            timeframe="15m",
            closes=[100.0, 101.0, 102.0, 103.0, 104.0],
            highs=[100.8, 101.8, 102.8, 103.8, 104.8],
            lows=[99.5, 100.5, 101.5, 102.5, 103.5],
            current_price=103.7,
            volume=1200.0,
        )
        zone = ZoneSignal(
            zone_low=102.9,
            zone_high=104.0,
            zone_type=ZoneType.DEMAND,
            freshness_score=0.8,
        )

        signal = evaluate_confluence(snapshot, zone)

        self.assertTrue(signal.is_valid)
        self.assertGreaterEqual(signal.confluence_score, 60)


if __name__ == "__main__":
    unittest.main()
