from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com"
DEFAULT_GEMINI_HEALTH_PATH = "/v1beta/models"


@dataclass(frozen=True)
class AIAnalystConnectivityStatus:
    provider: str
    enabled: bool
    configured: bool
    reachable: bool
    detail: str


class AIAnalystAdapter(Protocol):
    def check_connectivity(self) -> AIAnalystConnectivityStatus:
        ...


class DisabledAIAnalystAdapter:
    def __init__(self, provider: str = "none") -> None:
        self._provider = provider

    def check_connectivity(self) -> AIAnalystConnectivityStatus:
        return AIAnalystConnectivityStatus(
            provider=self._provider,
            enabled=False,
            configured=False,
            reachable=False,
            detail="disabled",
        )


class UnsupportedAIAnalystAdapter:
    def __init__(self, provider: str) -> None:
        self._provider = provider

    def check_connectivity(self) -> AIAnalystConnectivityStatus:
        return AIAnalystConnectivityStatus(
            provider=self._provider,
            enabled=True,
            configured=False,
            reachable=False,
            detail=f"unsupported provider: {self._provider}",
        )


class HttpAIAnalystAdapter:
    def __init__(
        self,
        provider: str,
        base_url: str,
        api_key: str,
        timeout_seconds: float = 10.0,
        health_path: str = "/health",
    ) -> None:
        self._provider = provider
        self._base_url = base_url.strip().rstrip("/")
        self._api_key = api_key.strip()
        self._timeout_seconds = timeout_seconds
        normalized_health_path = health_path.strip() or "/health"
        self._health_path = (
            normalized_health_path
            if normalized_health_path.startswith("/")
            else f"/{normalized_health_path}"
        )

    def check_connectivity(self) -> AIAnalystConnectivityStatus:
        if not self._base_url:
            return AIAnalystConnectivityStatus(
                provider=self._provider,
                enabled=True,
                configured=False,
                reachable=False,
                detail="missing ORACLE_AI_ANALYST_BASE_URL",
            )

        if not self._api_key:
            return AIAnalystConnectivityStatus(
                provider=self._provider,
                enabled=True,
                configured=False,
                reachable=False,
                detail="missing ORACLE_AI_ANALYST_API_KEY",
            )

        endpoint = f"{self._base_url}{self._health_path}"
        request = self._build_request(endpoint)

        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                body = response.read().decode("utf-8")
            return AIAnalystConnectivityStatus(
                provider=self._provider,
                enabled=True,
                configured=True,
                reachable=True,
                detail=_derive_health_detail(body),
            )
        except HTTPError as exc:
            return AIAnalystConnectivityStatus(
                provider=self._provider,
                enabled=True,
                configured=True,
                reachable=False,
                detail=f"http_error: {exc.code}",
            )
        except URLError as exc:
            return AIAnalystConnectivityStatus(
                provider=self._provider,
                enabled=True,
                configured=True,
                reachable=False,
                detail=f"network_error: {str(exc.reason)}",
            )
        except Exception as exc:
            return AIAnalystConnectivityStatus(
                provider=self._provider,
                enabled=True,
                configured=True,
                reachable=False,
                detail=f"error: {str(exc)}",
            )

    def _build_request(self, endpoint: str) -> Request:
        return Request(
            endpoint,
            method="GET",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Accept": "application/json",
                "User-Agent": "project-oracle/phase8-ai-check",
            },
        )


class GeminiAIAnalystAdapter(HttpAIAnalystAdapter):
    def _build_request(self, endpoint: str) -> Request:
        return Request(
            endpoint,
            method="GET",
            headers={
                "X-goog-api-key": self._api_key,
                "Accept": "application/json",
                "User-Agent": "project-oracle/phase8-ai-check",
            },
        )


def _derive_health_detail(response_body: str) -> str:
    try:
        payload = json.loads(response_body)
    except json.JSONDecodeError:
        return "ok"

    if not isinstance(payload, dict):
        return "ok"

    status_value = str(payload.get("status", "")).strip().lower()
    if status_value in {"ok", "healthy", "up"}:
        return "ok"
    if status_value:
        return f"status={status_value}"

    return "ok"


def _env_with_default(name: str, default: str) -> str:
    value = os.getenv(name, "").strip()
    return value or default


def build_ai_analyst_adapter_from_env() -> AIAnalystAdapter:
    enabled = os.getenv("ORACLE_ENABLE_AI_ANALYST_CONNECTIVITY", "false").lower() == "true"
    provider = os.getenv("ORACLE_AI_PROVIDER", "none").strip().lower()

    if not enabled:
        return DisabledAIAnalystAdapter(provider=provider)

    if provider == "gemini":
        return GeminiAIAnalystAdapter(
            provider=provider,
            base_url=_env_with_default("ORACLE_AI_ANALYST_BASE_URL", DEFAULT_GEMINI_BASE_URL),
            api_key=os.getenv("ORACLE_AI_ANALYST_API_KEY", ""),
            timeout_seconds=float(os.getenv("ORACLE_AI_ANALYST_TIMEOUT", "10.0")),
            health_path=_env_with_default("ORACLE_AI_ANALYST_HEALTH_PATH", DEFAULT_GEMINI_HEALTH_PATH),
        )

    if provider in {"grok", "custom"}:
        return HttpAIAnalystAdapter(
            provider=provider,
            base_url=os.getenv("ORACLE_AI_ANALYST_BASE_URL", ""),
            api_key=os.getenv("ORACLE_AI_ANALYST_API_KEY", ""),
            timeout_seconds=float(os.getenv("ORACLE_AI_ANALYST_TIMEOUT", "10.0")),
            health_path=os.getenv("ORACLE_AI_ANALYST_HEALTH_PATH", "/health"),
        )

    return UnsupportedAIAnalystAdapter(provider=provider or "unknown")
