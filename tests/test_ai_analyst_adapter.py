from __future__ import annotations

import os
import unittest
from unittest.mock import patch
from urllib.request import Request

from oracle.infrastructure.ai_analyst_adapter import (
    HttpAIAnalystAdapter,
    build_ai_analyst_adapter_from_env,
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


class AIAnalystAdapterTest(unittest.TestCase):
    def test_should_return_disabled_status_when_connectivity_check_is_off(self) -> None:
        with patch.dict(
            os.environ,
            {
                "ORACLE_ENABLE_AI_ANALYST_CONNECTIVITY": "false",
                "ORACLE_AI_PROVIDER": "grok",
            },
            clear=False,
        ):
            status = build_ai_analyst_adapter_from_env().check_connectivity()

        self.assertFalse(status.enabled)
        self.assertEqual(status.detail, "disabled")

    def test_should_report_unconfigured_when_api_key_is_missing(self) -> None:
        with patch.dict(
            os.environ,
            {
                "ORACLE_ENABLE_AI_ANALYST_CONNECTIVITY": "true",
                "ORACLE_AI_PROVIDER": "custom",
                "ORACLE_AI_ANALYST_BASE_URL": "https://example.local",
                "ORACLE_AI_ANALYST_API_KEY": "",
            },
            clear=False,
        ):
            status = build_ai_analyst_adapter_from_env().check_connectivity()

        self.assertTrue(status.enabled)
        self.assertFalse(status.configured)
        self.assertFalse(status.reachable)
        self.assertIn("ORACLE_AI_ANALYST_API_KEY", status.detail)

    @patch("oracle.infrastructure.ai_analyst_adapter.urlopen")
    def test_should_report_reachable_when_health_payload_is_healthy(self, mock_urlopen) -> None:
        mock_urlopen.return_value = _FakeResponse('{"status":"healthy"}')

        adapter = HttpAIAnalystAdapter(
            provider="custom",
            base_url="https://example.local",
            api_key="secret-token",
            timeout_seconds=1.0,
        )
        status = adapter.check_connectivity()

        self.assertTrue(status.enabled)
        self.assertTrue(status.configured)
        self.assertTrue(status.reachable)
        self.assertEqual(status.detail, "ok")

    @patch("oracle.infrastructure.ai_analyst_adapter.urlopen")
    def test_should_use_gemini_api_key_header_with_default_models_path(self, mock_urlopen) -> None:
        mock_urlopen.return_value = _FakeResponse('{"models": []}')

        with patch.dict(
            os.environ,
            {
                "ORACLE_ENABLE_AI_ANALYST_CONNECTIVITY": "true",
                "ORACLE_AI_PROVIDER": "gemini",
                "ORACLE_AI_ANALYST_API_KEY": "gemini-test-key",
                "ORACLE_AI_ANALYST_BASE_URL": "",
                "ORACLE_AI_ANALYST_HEALTH_PATH": "",
            },
            clear=False,
        ):
            status = build_ai_analyst_adapter_from_env().check_connectivity()

        self.assertTrue(status.enabled)
        self.assertTrue(status.configured)
        self.assertTrue(status.reachable)
        self.assertEqual(status.provider, "gemini")

        request_arg = mock_urlopen.call_args[0][0]
        self.assertIsInstance(request_arg, Request)
        self.assertIn("/v1beta/models", request_arg.full_url)
        request_headers = {k.lower(): v for k, v in request_arg.header_items()}
        self.assertEqual(request_headers.get("x-goog-api-key"), "gemini-test-key")
        self.assertNotIn("authorization", request_headers)

    def test_should_report_unsupported_provider(self) -> None:
        with patch.dict(
            os.environ,
            {
                "ORACLE_ENABLE_AI_ANALYST_CONNECTIVITY": "true",
                "ORACLE_AI_PROVIDER": "unknown-provider",
            },
            clear=False,
        ):
            status = build_ai_analyst_adapter_from_env().check_connectivity()

        self.assertTrue(status.enabled)
        self.assertFalse(status.configured)
        self.assertFalse(status.reachable)
        self.assertIn("unsupported provider", status.detail)


if __name__ == "__main__":
    unittest.main()
