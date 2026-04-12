from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from oracle.application.strategy_intelligence import (
    append_parameter_change_request,
    build_ai_review_packet,
    select_worst_trades,
    write_ai_review_packet,
)


class StrategyIntelligenceTest(unittest.TestCase):
    def test_should_select_lowest_quality_trades_first(self) -> None:
        events = [
            {"event_type": "position_closed", "payload": {"reason": "A"}},
            {"event_type": "trade_quality_assessed", "payload": {"quality_score": 70, "mae": 1, "mfe": 2}},
            {"event_type": "position_closed", "payload": {"reason": "B"}},
            {"event_type": "trade_quality_assessed", "payload": {"quality_score": 40, "mae": 2, "mfe": 1}},
        ]

        result = select_worst_trades(events, limit=1)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].quality_score, 40.0)
        self.assertEqual(result[0].close_reason, "B")

    def test_should_write_packet_and_registry_entry(self) -> None:
        events = [
            {"event_type": "position_closed", "payload": {"reason": "A"}},
            {"event_type": "trade_quality_assessed", "payload": {"quality_score": 50, "mae": 1, "mfe": 1}},
        ]
        packet = build_ai_review_packet(events, "grok", "paper", "testnet", limit=10)

        with tempfile.TemporaryDirectory() as temp_dir:
            packet_path = write_ai_review_packet(Path(temp_dir), packet)
            self.assertTrue(packet_path.exists())

            registry_file = Path(temp_dir) / "requests.jsonl"
            append_parameter_change_request(registry_file, {"status": "pending"})
            self.assertTrue(registry_file.exists())


if __name__ == "__main__":
    unittest.main()
