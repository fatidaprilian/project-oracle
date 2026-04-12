from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from oracle.application.strategy_intelligence import (
    append_parameter_change_request,
    build_parameter_change_request,
    build_ai_review_packet,
    select_worst_trades,
    summarize_parameter_change_registry,
    validate_suggested_changes,
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
            append_parameter_change_request(registry_file, {"status": "pending", "validation": {"is_valid": True}})
            self.assertTrue(registry_file.exists())

    def test_should_validate_range_and_unknown_parameters(self) -> None:
        violations = validate_suggested_changes(
            {
                "min_confluence_score": 120.0,
                "unknown_param": 1.0,
            }
        )

        self.assertEqual(len(violations), 2)
        self.assertTrue(any(item.startswith("OUT_OF_RANGE:min_confluence_score") for item in violations))
        self.assertTrue(any(item.startswith("UNKNOWN_PARAMETER:unknown_param") for item in violations))

    def test_should_build_request_with_validation_payload(self) -> None:
        request = build_parameter_change_request(
            generated_from="reports/ai-review/sample.json",
            provider="grok",
            status="approved",
            suggested_changes={
                "min_confluence_score": 60.0,
                "min_volume_threshold": 900.0,
                "max_consecutive_losses": 3.0,
            },
        )

        self.assertEqual(request["status"], "approved")
        self.assertTrue(request["validation"]["is_valid"])

    def test_should_summarize_registry_and_ready_to_promote(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_file = Path(temp_dir) / "requests.jsonl"
            append_parameter_change_request(
                registry_file,
                {
                    "status": "approved",
                    "validation": {"is_valid": True},
                },
            )
            append_parameter_change_request(
                registry_file,
                {
                    "status": "pending",
                    "validation": {"is_valid": True},
                },
            )

            summary = summarize_parameter_change_registry(registry_file)

            self.assertEqual(summary["total"], 2)
            self.assertEqual(summary["approved"], 1)
            self.assertEqual(summary["pending"], 1)
            self.assertEqual(summary["ready_to_promote"], 1)


if __name__ == "__main__":
    unittest.main()
