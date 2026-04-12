from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from oracle.application.weekly_report import build_weekly_report, write_weekly_report


class WeeklyReportTest(unittest.TestCase):
    def test_should_include_rejection_and_close_sections(self) -> None:
        events = [
            {"event_type": "candidate_rejected", "payload": {"reason": ["LOW_CONFLUENCE"]}},
            {"event_type": "position_closed", "payload": {"reason": "FIB_EXTENSION_TP_HIT"}},
            {
                "event_type": "trade_quality_assessed",
                "payload": {"quality_score": 62.5, "mae": 1.2, "mfe": 2.1},
            },
        ]

        report = build_weekly_report(events)

        self.assertIn("Top Rejection Reasons", report)
        self.assertIn("LOW_CONFLUENCE", report)
        self.assertIn("FIB_EXTENSION_TP_HIT", report)
        self.assertIn("Trade Quality", report)
        self.assertIn("avg_quality_score", report)

    def test_should_write_markdown_file_to_output_dir(self) -> None:
        events = [{"event_type": "candidate_rejected", "payload": {"reason": "LOW_LIQUIDITY"}}]
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = write_weekly_report(Path(temp_dir), events)

            self.assertTrue(report_path.exists())
            self.assertEqual(report_path.suffix, ".md")


if __name__ == "__main__":
    unittest.main()
