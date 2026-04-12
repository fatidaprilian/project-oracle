from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ExternalSentimentConfig:
    base_url: str
    api_key: str
    timeout_seconds: float = 5.0

    @staticmethod
    def from_env() -> "ExternalSentimentConfig":
        return ExternalSentimentConfig(
            base_url=os.getenv("ORACLE_SENTIMENT_BASE_URL", ""),
            api_key=os.getenv("ORACLE_SENTIMENT_API_KEY", ""),
            timeout_seconds=float(os.getenv("ORACLE_SENTIMENT_TIMEOUT", "5.0")),
        )


class ExternalSentimentProvider:
    def __init__(self, config: ExternalSentimentConfig) -> None:
        self._config = config

    def get_sentiment_bias(self, symbol: str) -> str:
        payload = self._safe_get_json("/sentiment", symbol)
        value = str(payload.get("bias", "neutral")).lower()
        if value not in {"bullish", "bearish", "neutral"}:
            return "neutral"
        return value

    def get_event_risk_level(self, symbol: str) -> str:
        payload = self._safe_get_json("/event-risk", symbol)
        value = str(payload.get("risk_level", "low")).lower()
        if value not in {"low", "medium", "high", "critical"}:
            return "low"
        return value

    def _safe_get_json(self, path: str, symbol: str) -> dict[str, Any]:
        if not self._config.base_url or not self._config.api_key:
            return {}

        query = urlencode({"symbol": symbol})
        url = f"{self._config.base_url.rstrip('/')}{path}?{query}"
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Accept": "application/json",
        }
        request = Request(url, headers=headers, method="GET")

        try:
            with urlopen(request, timeout=self._config.timeout_seconds) as response:
                body = response.read().decode("utf-8")
                decoded = json.loads(body)
                if isinstance(decoded, dict):
                    return decoded
                return {}
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            return {}
