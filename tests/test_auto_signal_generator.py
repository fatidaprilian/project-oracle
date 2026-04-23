from __future__ import annotations

import sys
import unittest

sys.path.insert(0, "src")

from oracle.application.signal_timing import (
    normalize_estimated_duration_window,
)


class AutoSignalDurationWindowTest(unittest.TestCase):
    def test_should_clamp_and_order_buy_duration_window(self) -> None:
        min_days, max_days = normalize_estimated_duration_window(
            raw_min_days=9,
            raw_max_days=3,
            bias="BUY",
            confluence_score=88,
            has_quant_entry_plan=True,
        )

        self.assertEqual(min_days, 9)
        self.assertEqual(max_days, 9)

    def test_should_fallback_to_default_duration_window_when_input_is_missing(self) -> None:
        min_days, max_days = normalize_estimated_duration_window(
            raw_min_days=None,
            raw_max_days=None,
            bias="BUY",
            confluence_score=82,
            has_quant_entry_plan=True,
        )

        self.assertEqual((min_days, max_days), (3, 5))

    def test_should_return_none_for_non_actionable_bias(self) -> None:
        min_days, max_days = normalize_estimated_duration_window(
            raw_min_days=2,
            raw_max_days=5,
            bias="IGNORE",
            confluence_score=50,
            has_quant_entry_plan=False,
        )

        self.assertIsNone(min_days)
        self.assertIsNone(max_days)


if __name__ == "__main__":
    unittest.main()
