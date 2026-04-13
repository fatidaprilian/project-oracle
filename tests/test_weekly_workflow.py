from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from oracle.application.weekly_workflow import run_weekly_workflow


class WeeklyWorkflowTest(unittest.TestCase):
    def test_should_run_complete_workflow_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dataset_path = Path("data/replay/sample_snapshots.jsonl")
            registry_file = Path(temp_dir) / "requests.jsonl"
            ai_review_dir = Path(temp_dir) / "ai-review"
            weekly_dir = Path(temp_dir) / "weekly"
            config_dir = Path(temp_dir) / "configs"

            result = run_weekly_workflow(
                dataset_path=dataset_path,
                registry_file=registry_file,
                ai_review_output_dir=ai_review_dir,
                weekly_output_dir=weekly_dir,
                strategy_config_output_dir=config_dir,
            )

            self.assertTrue(result.success)
            self.assertIsNotNone(result.ai_review_packet_path)
            self.assertIsNotNone(result.weekly_report_path)
            self.assertIsNotNone(result.governance_summary)
            self.assertTrue(result.ai_review_packet_path.exists())
            self.assertTrue(result.weekly_report_path.exists())
            self.assertEqual(result.governance_summary["total"], 1)
            self.assertEqual(result.governance_summary["pending"], 1)
            self.assertEqual(result.governance_summary["approved"], 0)
            self.assertEqual(result.governance_summary["ready_to_promote"], 0)

    def test_should_capture_workflow_errors_gracefully(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_dataset = Path(temp_dir) / "nonexistent.jsonl"
            registry_file = Path(temp_dir) / "requests.jsonl"
            ai_review_dir = Path(temp_dir) / "ai-review"
            weekly_dir = Path(temp_dir) / "weekly"
            config_dir = Path(temp_dir) / "configs"

            result = run_weekly_workflow(
                dataset_path=nonexistent_dataset,
                registry_file=registry_file,
                ai_review_output_dir=ai_review_dir,
                weekly_output_dir=weekly_dir,
                strategy_config_output_dir=config_dir,
            )

            self.assertFalse(result.success)
            self.assertIsNotNone(result.error)
            self.assertTrue(any("failed" in detail.lower()
                            for detail in result.details))

    def test_should_record_symbol_when_workflow_runs_with_symbol_filter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dataset_path = Path("data/replay/sample_snapshots.jsonl")
            registry_file = Path(temp_dir) / "requests.jsonl"
            ai_review_dir = Path(temp_dir) / "ai-review"
            weekly_dir = Path(temp_dir) / "weekly"
            config_dir = Path(temp_dir) / "configs"

            result = run_weekly_workflow(
                dataset_path=dataset_path,
                symbol="BTCUSDT",
                registry_file=registry_file,
                ai_review_output_dir=ai_review_dir,
                weekly_output_dir=weekly_dir,
                strategy_config_output_dir=config_dir,
            )

            self.assertTrue(result.success)
            with registry_file.open("r", encoding="utf-8") as file_obj:
                records = [json.loads(line) for line in file_obj if line.strip()]

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].get("symbol"), "BTCUSDT")


if __name__ == "__main__":
    unittest.main()
