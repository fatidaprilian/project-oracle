from __future__ import annotations

import unittest

from oracle.modules.sentiment_gate import evaluate_sentiment


class _HighRiskProvider:
    def get_sentiment_bias(self, symbol: str) -> str:
        return "bearish"

    def get_event_risk_level(self, symbol: str) -> str:
        return "high"


class SentimentGateTest(unittest.TestCase):
    def test_should_enable_shield_when_risk_is_high(self) -> None:
        signal = evaluate_sentiment("BTCUSDT", _HighRiskProvider())

        self.assertTrue(signal.shield_status)
        self.assertEqual(signal.event_risk_level, "high")


if __name__ == "__main__":
    unittest.main()
