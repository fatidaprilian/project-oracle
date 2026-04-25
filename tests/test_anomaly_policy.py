from __future__ import annotations

import sys
import unittest

sys.path.insert(0, "src")

from oracle.application.anomaly_policy import classify_volume_anomaly


class AnomalyPolicyTest(unittest.TestCase):
    def test_should_classify_confirmed_volume_expansion_as_momentum_watch(self) -> None:
        decision = classify_volume_anomaly(
            close_price=180,
            volume_ratio=8.5,
            change_pct=4.2,
        )

        self.assertEqual(decision.lane, "MOMENTUM_WATCH")
        self.assertEqual(decision.reason, "VOLUME_EXPANSION_WITH_PRICE_CONFIRMATION")
        self.assertGreater(decision.discovery_score, 0)

    def test_should_keep_extended_price_move_out_of_action_lane(self) -> None:
        decision = classify_volume_anomaly(
            close_price=180,
            volume_ratio=12,
            change_pct=22,
        )

        self.assertEqual(decision.lane, "EXTENDED_RISK")
        self.assertEqual(decision.reason, "PRICE_ALREADY_EXTENDED")

    def test_should_keep_low_price_anomaly_as_radar_only(self) -> None:
        decision = classify_volume_anomaly(
            close_price=42,
            volume_ratio=9,
            change_pct=5,
        )

        self.assertEqual(decision.lane, "RADAR_ONLY")
        self.assertEqual(decision.reason, "LOW_PRICE_LIQUIDITY_RISK")


if __name__ == "__main__":
    unittest.main()
