from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, "src")

from oracle.application.auto_signal_policy import is_conservative_entry_candidate
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


class AutoSignalConservativeGateTest(unittest.TestCase):
    def _quant_results(
        self,
        *,
        tradeable: bool = True,
        regime: str = "uptrend",
        confluence_score: float = 86.0,
        pullback_valid: bool = True,
        entry_valid: bool = True,
    ) -> dict:
        return {
            "structure": SimpleNamespace(
                is_tradeable=tradeable,
                market_regime=SimpleNamespace(value=regime),
            ),
            "confluence": SimpleNamespace(confluence_score=confluence_score),
            "pullback": SimpleNamespace(is_valid=pullback_valid),
            "entry_plan": SimpleNamespace(should_place_order=entry_valid),
        }

    def test_should_accept_only_fully_confirmed_entry_candidate(self) -> None:
        with patch.dict("os.environ", {"ORACLE_AUTO_SIGNAL_MIN_CONFLUENCE": "80"}):
            is_candidate, rejection_reasons = is_conservative_entry_candidate(
                self._quant_results()
            )

        self.assertTrue(is_candidate)
        self.assertEqual(rejection_reasons, [])

    def test_should_reject_quant_rejected_setup_before_gemini(self) -> None:
        with patch.dict("os.environ", {"ORACLE_AUTO_SIGNAL_MIN_CONFLUENCE": "80"}):
            is_candidate, rejection_reasons = is_conservative_entry_candidate(
                self._quant_results(pullback_valid=False, entry_valid=False)
            )

        self.assertFalse(is_candidate)
        self.assertIn("PULLBACK_NOT_CONFIRMED", rejection_reasons)
        self.assertIn("ENTRY_PLAN_REJECTED", rejection_reasons)

    def test_should_reject_low_confluence_setup_before_gemini(self) -> None:
        with patch.dict("os.environ", {"ORACLE_AUTO_SIGNAL_MIN_CONFLUENCE": "85"}):
            is_candidate, rejection_reasons = is_conservative_entry_candidate(
                self._quant_results(confluence_score=82.0)
            )

        self.assertFalse(is_candidate)
        self.assertIn("CONFLUENCE_BELOW_85", rejection_reasons)


if __name__ == "__main__":
    unittest.main()
