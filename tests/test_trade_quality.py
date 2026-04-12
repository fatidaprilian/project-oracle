from __future__ import annotations

import unittest

from oracle.application.trade_quality import evaluate_trade_quality
from oracle.domain.models import MarketSnapshot, PositionState


class TradeQualityTest(unittest.TestCase):
    def test_should_compute_mae_mfe_and_quality_for_long_position(self) -> None:
        snapshot = MarketSnapshot(
            symbol="BTCUSDT",
            timeframe="15m",
            closes=[100.0, 101.0, 102.0, 103.0],
            highs=[100.5, 101.8, 103.2, 104.0],
            lows=[99.0, 99.8, 100.4, 101.1],
            current_price=103.2,
            volume=1000.0,
        )
        position = PositionState(
            symbol="BTCUSDT",
            side="long",
            entry_price=101.0,
            stop_loss=99.5,
            take_profit_primary=103.0,
            take_profit_secondary=104.0,
        )

        metrics = evaluate_trade_quality(snapshot, position)

        self.assertEqual(metrics.mae, 2.0)
        self.assertEqual(metrics.mfe, 3.0)
        self.assertEqual(metrics.quality_score, 60.0)


if __name__ == "__main__":
    unittest.main()
