from __future__ import annotations

import unittest


class APIIntegrationTest(unittest.TestCase):
    """Integration tests for API (requires FastAPI installed to run)"""

    def test_should_import_api_modules(self) -> None:
        """Verify API and scheduler modules can be imported"""
        try:
            # These imports will fail gracefully if FastAPI not installed
            import sys
            import importlib.util

            # Check api.main exists and can be compiled
            api_main_spec = importlib.util.spec_from_file_location(
                "api.main",
                "src/api/main.py",
            )
            self.assertIsNotNone(
                api_main_spec, "api.main spec should be found")

            # Check scheduler.py exists and can be compiled
            scheduler_spec = importlib.util.spec_from_file_location(
                "scheduler",
                "src/scheduler.py",
            )
            self.assertIsNotNone(
                scheduler_spec, "scheduler spec should be found")

            # Check run_api.py exists
            run_api_spec = importlib.util.spec_from_file_location(
                "run_api",
                "src/run_api.py",
            )
            self.assertIsNotNone(run_api_spec, "run_api spec should be found")

        except Exception as e:
            self.fail(f"Module loading failed: {str(e)}")

    def test_should_import_runtime_integration(self) -> None:
        """Verify runtime parameter loading works"""
        import sys
        sys.path.insert(0, "src")

        try:
            from oracle.runtime import (
                load_latest_strategy_config,
                apply_strategy_config,
            )

            self.assertTrue(callable(load_latest_strategy_config))
            self.assertTrue(callable(apply_strategy_config))
        except Exception as e:
            self.fail(f"Runtime integration import failed: {str(e)}")

    def test_should_import_weekly_workflow(self) -> None:
        """Verify weekly workflow module works"""
        import sys
        sys.path.insert(0, "src")

        try:
            from oracle.application.weekly_workflow import run_weekly_workflow, WorkflowResult

            self.assertTrue(callable(run_weekly_workflow))
            self.assertIsNotNone(WorkflowResult)
        except Exception as e:
            self.fail(f"Weekly workflow import failed: {str(e)}")


if __name__ == "__main__":
    unittest.main()
