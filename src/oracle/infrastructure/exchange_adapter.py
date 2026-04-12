from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_BYBIT_TESTNET_BASE_URL = "https://api-testnet.bybit.com"
DEFAULT_BYBIT_MAINNET_BASE_URL = "https://api.bybit.com"


@dataclass(frozen=True)
class ExchangeConnectivityStatus:
    provider: str
    enabled: bool
    configured: bool
    reachable: bool
    detail: str
    server_time: str | None = None


class ExchangeAdapter(Protocol):
    def check_connectivity(self) -> ExchangeConnectivityStatus:
        ...


class DisabledExchangeAdapter:
    def __init__(self, provider: str = "none") -> None:
        self._provider = provider

    def check_connectivity(self) -> ExchangeConnectivityStatus:
        return ExchangeConnectivityStatus(
            provider=self._provider,
            enabled=False,
            configured=False,
            reachable=False,
            detail="disabled",
        )


class UnsupportedExchangeAdapter:
    def __init__(self, provider: str) -> None:
        self._provider = provider

    def check_connectivity(self) -> ExchangeConnectivityStatus:
        return ExchangeConnectivityStatus(
            provider=self._provider,
            enabled=True,
            configured=False,
            reachable=False,
            detail=f"unsupported provider: {self._provider}",
        )


class BybitExchangeAdapter:
    def __init__(self, base_url: str, timeout_seconds: float = 3.0) -> None:
        self._base_url = base_url.strip().rstrip("/")
        self._timeout_seconds = timeout_seconds

    def check_connectivity(self) -> ExchangeConnectivityStatus:
        if not self._base_url:
            return ExchangeConnectivityStatus(
                provider="bybit",
                enabled=True,
                configured=False,
                reachable=False,
                detail="missing ORACLE_EXCHANGE_BASE_URL",
            )

        endpoint = f"{self._base_url}/v5/market/time"
        request = Request(
            endpoint,
            method="GET",
            headers={"User-Agent": "project-oracle/phase8-check"},
        )

        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                body = response.read().decode("utf-8")
            payload = json.loads(body)
            ret_code = int(payload.get("retCode", -1))
            ret_msg = str(payload.get("retMsg", ""))

            if ret_code != 0:
                return ExchangeConnectivityStatus(
                    provider="bybit",
                    enabled=True,
                    configured=True,
                    reachable=False,
                    detail=f"retCode={ret_code} retMsg={ret_msg}",
                )

            result = payload.get("result", {})
            server_time = None
            if isinstance(result, dict):
                time_second = result.get("timeSecond")
                time_nano = result.get("timeNano")
                server_time = str(time_second or time_nano or "") or None

            return ExchangeConnectivityStatus(
                provider="bybit",
                enabled=True,
                configured=True,
                reachable=True,
                detail="ok",
                server_time=server_time,
            )
        except HTTPError as exc:
            return ExchangeConnectivityStatus(
                provider="bybit",
                enabled=True,
                configured=True,
                reachable=False,
                detail=f"http_error: {exc.code}",
            )
        except URLError as exc:
            return ExchangeConnectivityStatus(
                provider="bybit",
                enabled=True,
                configured=True,
                reachable=False,
                detail=f"network_error: {str(exc.reason)}",
            )
        except Exception as exc:
            return ExchangeConnectivityStatus(
                provider="bybit",
                enabled=True,
                configured=True,
                reachable=False,
                detail=f"error: {str(exc)}",
            )


def build_exchange_adapter_from_env() -> ExchangeAdapter:
    enabled = os.getenv("ORACLE_ENABLE_EXCHANGE_CONNECTIVITY", "false").lower() == "true"
    provider = os.getenv("ORACLE_EXCHANGE_PROVIDER", "none").strip().lower()
    exchange_env = os.getenv("ORACLE_EXCHANGE_ENV", "testnet").strip().lower()

    if not enabled:
        return DisabledExchangeAdapter(provider=provider)

    if provider == "bybit":
        default_url = (
            DEFAULT_BYBIT_TESTNET_BASE_URL
            if exchange_env == "testnet"
            else DEFAULT_BYBIT_MAINNET_BASE_URL
        )
        base_url = os.getenv("ORACLE_EXCHANGE_BASE_URL", default_url).strip()
        timeout_seconds = float(os.getenv("ORACLE_EXCHANGE_TIMEOUT_SECONDS", "3.0"))
        return BybitExchangeAdapter(base_url=base_url, timeout_seconds=timeout_seconds)

    return UnsupportedExchangeAdapter(provider=provider or "unknown")
