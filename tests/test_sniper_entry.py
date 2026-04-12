from __future__ import annotations

import unittest

from oracle.domain.models import ConfluenceSignal, MarketSnapshot, SentimentSignal, ZoneSignal, ZoneType
from oracle.modules.sniper_entry import build_entry_plan


class SniperEntryTest(unittest.TestCase):
    def test_should_reject_when_news_shield_active(self) -> None:
        snapshot = MarketSnapshot(
            symbol="BTCUSDT",
            timeframe="15m",
            closes=[100.0, 101.0, 102.0],
            highs=[100.5, 101.5, 102.5],
            lows=[99.5, 100.5, 101.5],
            current_price=101.7,
            volume=1000.0,
        )
        zone = ZoneSignal(101.0, 102.0, ZoneType.DEMAND, 0.7)
        confluence = ConfluenceSignal(80.0, 101.4, 101.6, True)
        sentiment = SentimentSignal("bearish", "high", True)

        plan = build_entry_plan(snapshot, zone, confluence, sentiment)

        self.assertFalse(plan.should_place_order)
        self.assertIn("NEWS_SHIELD_ACTIVE", plan.reason_codes)


if __name__ == "__main__":
    unittest.main()
