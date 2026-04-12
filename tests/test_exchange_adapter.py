from __future__ import annotations

import os
import unittest
from unittest.mock import patch
from urllib.request import Request

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

    def test_should_report_account_unconfigured_when_api_key_missing(self) -> None:
        with patch.dict(
            os.environ,
            {
                "ORACLE_ENABLE_EXCHANGE_CONNECTIVITY": "true",
                "ORACLE_EXCHANGE_PROVIDER": "bybit",
                "ORACLE_EXCHANGE_BASE_URL": "https://api-testnet.bybit.com",
                "ORACLE_EXCHANGE_API_KEY": "",
                "ORACLE_EXCHANGE_API_SECRET": "secret",
            },
            clear=False,
        ):
            status = build_exchange_adapter_from_env().check_account_connectivity()

        self.assertTrue(status.enabled)
        self.assertFalse(status.configured)
        self.assertFalse(status.reachable)
        self.assertIn("ORACLE_EXCHANGE_API_KEY", status.detail)

    @patch("oracle.infrastructure.exchange_adapter.time.time", return_value=1712921005.0)
    @patch("oracle.infrastructure.exchange_adapter.urlopen")
    def test_should_report_bybit_account_reachable_when_retcode_zero(self, mock_urlopen, _mock_time) -> None:
        mock_urlopen.return_value = _FakeResponse('{"retCode":0,"retMsg":"OK","result":{}}')

        adapter = BybitExchangeAdapter(
            "https://api-testnet.bybit.com",
            timeout_seconds=1.0,
            api_key="test-key",
            api_secret="test-secret",
            account_type="UNIFIED",
        )
        status = adapter.check_account_connectivity()

        self.assertTrue(status.enabled)
        self.assertTrue(status.configured)
        self.assertTrue(status.reachable)
        self.assertEqual(status.detail, "ok")
        self.assertEqual(status.account_type, "UNIFIED")

        request_arg = mock_urlopen.call_args[0][0]
        self.assertIsInstance(request_arg, Request)
        self.assertIn("/v5/account/wallet-balance?accountType=UNIFIED", request_arg.full_url)
        headers = {k.lower(): v for k, v in request_arg.header_items()}
        self.assertEqual(headers.get("x-bapi-api-key"), "test-key")
        self.assertEqual(headers.get("x-bapi-sign-type"), "2")
        self.assertIn("x-bapi-sign", headers)

    def test_should_report_account_unsupported_provider(self) -> None:
        with patch.dict(
            os.environ,
            {
                "ORACLE_ENABLE_EXCHANGE_CONNECTIVITY": "true",
                "ORACLE_EXCHANGE_PROVIDER": "unknown-provider",
            },
            clear=False,
        ):
            status = build_exchange_adapter_from_env().check_account_connectivity()

        self.assertTrue(status.enabled)
        self.assertFalse(status.configured)
        self.assertFalse(status.reachable)
        self.assertIn("unsupported provider", status.detail)


if __name__ == "__main__":
    unittest.main()
