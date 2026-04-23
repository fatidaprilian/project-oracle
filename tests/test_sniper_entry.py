from __future__ import annotations

import unittest

from oracle.domain.models import ConfluenceSignal, MarketSnapshot, PullbackSignal, SentimentSignal, ZoneSignal, ZoneType
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

    def test_should_reject_when_pullback_confluence_is_invalid(self) -> None:
        snapshot = MarketSnapshot(
            symbol="AAPL",
            timeframe="1h",
            closes=[100.0, 101.0, 102.0],
            highs=[100.5, 101.5, 102.5],
            lows=[99.5, 100.5, 101.5],
            current_price=101.7,
            volume=1000.0,
        )
        zone = ZoneSignal(101.0, 102.0, ZoneType.DEMAND, 0.7)
        confluence = ConfluenceSignal(80.0, 101.4, 101.6, True)
        sentiment = SentimentSignal("bullish", "low", False)
        pullback = PullbackSignal(
            is_valid=False,
            strategy_name="NONE",
            confidence_score=20.0,
            ema_200=100.0,
            ma_99=101.0,
            volume_ratio=1.0,
            reason_codes=["VOLUME_BELOW_1P2_MA20"],
        )

        plan = build_entry_plan(snapshot, zone, confluence, sentiment, pullback)

        self.assertFalse(plan.should_place_order)
        self.assertIn("PULLBACK_CONFLUENCE_FAIL", plan.reason_codes)


if __name__ == "__main__":
    unittest.main()
