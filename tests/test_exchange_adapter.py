from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from oracle.infrastructure.exchange_adapter import (
    BybitExchangeAdapter,
    build_exchange_adapter_from_env,
)


class _FakeResponse:
    def __init__(self, body: str) -> None:
        self._body = body.encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class ExchangeAdapterTest(unittest.TestCase):
    def test_should_return_disabled_status_when_exchange_check_is_off(self) -> None:
        with patch.dict(
            os.environ,
            {
                "ORACLE_ENABLE_EXCHANGE_CONNECTIVITY": "false",
                "ORACLE_EXCHANGE_PROVIDER": "bybit",
            },
            clear=False,
        ):
            status = build_exchange_adapter_from_env().check_connectivity()

        self.assertFalse(status.enabled)
        self.assertEqual(status.detail, "disabled")

    @patch("oracle.infrastructure.exchange_adapter.urlopen")
    def test_should_report_bybit_reachable_on_retcode_zero(self, mock_urlopen) -> None:
        mock_urlopen.return_value = _FakeResponse(
            '{"retCode":0,"retMsg":"OK","result":{"timeSecond":"1712921005"}}'
        )

        adapter = BybitExchangeAdapter("https://api-testnet.bybit.com", timeout_seconds=1.0)
        status = adapter.check_connectivity()

        self.assertTrue(status.enabled)
        self.assertTrue(status.configured)
        self.assertTrue(status.reachable)
        self.assertEqual(status.detail, "ok")
        self.assertEqual(status.server_time, "1712921005")

    @patch("oracle.infrastructure.exchange_adapter.urlopen")
    def test_should_report_bybit_unreachable_on_nonzero_retcode(self, mock_urlopen) -> None:
        mock_urlopen.return_value = _FakeResponse(
            '{"retCode":10001,"retMsg":"Bad request","result":{}}'
        )

        adapter = BybitExchangeAdapter("https://api-testnet.bybit.com", timeout_seconds=1.0)
        status = adapter.check_connectivity()

        self.assertTrue(status.enabled)
        self.assertTrue(status.configured)
        self.assertFalse(status.reachable)
        self.assertIn("retCode=10001", status.detail)

    def test_should_report_unsupported_provider(self) -> None:
        with patch.dict(
            os.environ,
            {
                "ORACLE_ENABLE_EXCHANGE_CONNECTIVITY": "true",
                "ORACLE_EXCHANGE_PROVIDER": "unknown-provider",
            },
            clear=False,
        ):
            status = build_exchange_adapter_from_env().check_connectivity()

        self.assertTrue(status.enabled)
        self.assertFalse(status.configured)
        self.assertFalse(status.reachable)
        self.assertIn("unsupported provider", status.detail)


if __name__ == "__main__":
    unittest.main()
