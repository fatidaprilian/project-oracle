from __future__ import annotations

import os
import unittest
from datetime import date
from unittest.mock import patch


def _import_api_main_or_skip(test_case: unittest.TestCase):
    try:
        from api import main as api_main  # pylint: disable=import-outside-toplevel
        return api_main
    except ModuleNotFoundError as exc:
        test_case.skipTest(f"api.main import skipped due to missing dependency: {exc}")


def _import_auto_signal_generator_or_skip(test_case: unittest.TestCase):
    try:
        from oracle.application import auto_signal_generator  # pylint: disable=import-outside-toplevel
        return auto_signal_generator
    except ModuleNotFoundError as exc:
        test_case.skipTest(
            "auto_signal_generator import skipped due to missing dependency: "
            f"{exc}"
        )


class DailyAnalysisPolicyApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.api_main = _import_api_main_or_skip(self)
        self.api_main._LAST_ANALYSIS_DAY_BY_TICKER.clear()

    def test_should_limit_same_ticker_once_per_day_with_in_memory_guard(self) -> None:
        with patch.dict(os.environ, {"ORACLE_ENABLE_POSTGRES": "false"}, clear=False):
            self.assertFalse(self.api_main._has_reached_daily_analysis_limit("AAPL"))

            self.api_main._mark_analyzed_today("AAPL")

            self.assertTrue(self.api_main._has_reached_daily_analysis_limit("AAPL"))
            self.assertFalse(self.api_main._has_reached_daily_analysis_limit("NVDA"))

    def test_should_use_database_guard_when_postgres_enabled(self) -> None:
        with patch.dict(os.environ, {"ORACLE_ENABLE_POSTGRES": "true"}, clear=False):
            with patch("oracle.infrastructure.postgres_repository.has_signal_today", return_value=True):
                self.assertTrue(self.api_main._has_reached_daily_analysis_limit("AAPL"))


class DailyAnalysisPolicyAutoSignalTest(unittest.TestCase):
    def setUp(self) -> None:
        self.auto_signal_generator = _import_auto_signal_generator_or_skip(self)
        self.auto_signal_generator._LAST_ANALYSIS_DAY_BY_TICKER.clear()

    def test_should_mark_all_candidates_as_analyzed_for_the_same_day(self) -> None:
        current_day = date(2026, 4, 23)
        candidates = ["AAPL", "AAPL.JK"]

        self.assertFalse(
            self.auto_signal_generator._is_already_analyzed_today(candidates, current_day)
        )

        self.auto_signal_generator._mark_analyzed_today(candidates, current_day)

        self.assertTrue(
            self.auto_signal_generator._is_already_analyzed_today(["AAPL"], current_day)
        )
        self.assertTrue(
            self.auto_signal_generator._is_already_analyzed_today(["AAPL.JK"], current_day)
        )


if __name__ == "__main__":
    unittest.main()
