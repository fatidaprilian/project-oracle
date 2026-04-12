from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from oracle.application.risk_controls import RiskConfig
from oracle.runtime import apply_strategy_config, load_latest_strategy_config


class RuntimeStrategyConfigTest(unittest.TestCase):
    def test_should_load_latest_strategy_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            # Create two config files
            config1_path = config_dir / "v1-aaa.json"
            config2_path = config_dir / "v1-bbb.json"

            config1_path.write_text(json.dumps({"max_daily_loss_r": 2.5}))
            config2_path.write_text(json.dumps({"max_daily_loss_r": 3.0}))

            result = load_latest_strategy_config(config_dir)

            self.assertIsNotNone(result)
            self.assertEqual(result["max_daily_loss_r"], 3.0)

    def test_should_return_none_when_no_configs_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            result = load_latest_strategy_config(config_dir)

            self.assertIsNone(result)

    def test_should_return_none_when_dir_not_exists(self) -> None:
        result = load_latest_strategy_config(Path("/nonexistent/path"))

        self.assertIsNone(result)

    def test_should_apply_risk_parameters_from_config(self) -> None:
        base_config = RiskConfig()
        strategy_config = {
            "max_daily_loss_r": 2.0,
            "max_consecutive_losses": 2,
        }

        result = apply_strategy_config(base_config, strategy_config)

        self.assertEqual(result.max_daily_loss_r, 2.0)
        self.assertEqual(result.max_consecutive_losses, 2)

    def test_should_ignore_unknown_parameters(self) -> None:
        base_config = RiskConfig()
        strategy_config = {
            "max_daily_loss_r": 2.0,
            "unknown_param": "ignored",
        }

        result = apply_strategy_config(base_config, strategy_config)

        self.assertEqual(result.max_daily_loss_r, 2.0)

    def test_should_handle_invalid_parameter_values(self) -> None:
        base_config = RiskConfig()
        original_value = base_config.max_daily_loss_r

        strategy_config = {
            "max_daily_loss_r": "not_a_number",
        }

        result = apply_strategy_config(base_config, strategy_config)

        # Should keep original value if conversion fails
        self.assertEqual(result.max_daily_loss_r, original_value)

    def test_should_return_original_config_if_none_passed(self) -> None:
        base_config = RiskConfig()
        original_value = base_config.max_daily_loss_r

        result = apply_strategy_config(base_config, None)

        self.assertEqual(result.max_daily_loss_r, original_value)


if __name__ == "__main__":
    unittest.main()
