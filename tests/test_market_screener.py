from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, "src")

from oracle.application.message_formats import format_daily_broadcast_message


class MarketScreenerBroadcastTest(unittest.TestCase):
    def test_should_format_radar_message_without_one_day_target_claim(self) -> None:
        now_wib = datetime(2026, 4, 23, 16, 30, tzinfo=timezone.utc)

        message = format_daily_broadcast_message(
            anomalies=["ATLA.JK", "MAXI.JK", "ADCP.JK"],
            now_wib=now_wib,
        )

        self.assertIn("RADAR ORACLE SESI BERIKUTNYA", message)
        self.assertIn("ATLA", message)
        self.assertIn("MAXI", message)
        self.assertNotIn(".JK", message)
        self.assertIn("bukan target pergerakan satu hari", message)
        self.assertNotIn("POTENSI SAHAM BESOK", message)


if __name__ == "__main__":
    unittest.main()
