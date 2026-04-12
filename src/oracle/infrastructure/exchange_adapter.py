from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import os
import time
from typing import Protocol
from urllib.parse import urlencode
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


@dataclass(frozen=True)
class ExchangeAccountConnectivityStatus:
    provider: str
    enabled: bool
    configured: bool
    reachable: bool
    detail: str
    account_type: str | None = None


class ExchangeAdapter(Protocol):
    def check_connectivity(self) -> ExchangeConnectivityStatus:
        ...

    def check_account_connectivity(self) -> ExchangeAccountConnectivityStatus:
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

    def check_account_connectivity(self) -> ExchangeAccountConnectivityStatus:
        return ExchangeAccountConnectivityStatus(
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

    def check_account_connectivity(self) -> ExchangeAccountConnectivityStatus:
        return ExchangeAccountConnectivityStatus(
            provider=self._provider,
            enabled=True,
            configured=False,
            reachable=False,
            detail=f"unsupported provider: {self._provider}",
        )


class BybitExchangeAdapter:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 3.0,
        api_key: str = "",
        api_secret: str = "",
        recv_window: int = 5000,
        account_type: str = "UNIFIED",
    ) -> None:
        self._base_url = base_url.strip().rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._api_key = api_key.strip()
        self._api_secret = api_secret.strip()
        self._recv_window = recv_window
        self._account_type = account_type.strip().upper() or "UNIFIED"

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

    def check_account_connectivity(self) -> ExchangeAccountConnectivityStatus:
        if not self._base_url:
            return ExchangeAccountConnectivityStatus(
                provider="bybit",
                enabled=True,
                configured=False,
                reachable=False,
                detail="missing ORACLE_EXCHANGE_BASE_URL",
            )

        if not self._api_key:
            return ExchangeAccountConnectivityStatus(
                provider="bybit",
                enabled=True,
                configured=False,
                reachable=False,
                detail="missing ORACLE_EXCHANGE_API_KEY",
                account_type=self._account_type,
            )

        if not self._api_secret:
            return ExchangeAccountConnectivityStatus(
                provider="bybit",
                enabled=True,
                configured=False,
                reachable=False,
                detail="missing ORACLE_EXCHANGE_API_SECRET",
                account_type=self._account_type,
            )

        endpoint_path = "/v5/account/wallet-balance"
        query_string = urlencode({"accountType": self._account_type})
        timestamp = str(int(time.time() * 1000))
        pre_sign = f"{timestamp}{self._api_key}{self._recv_window}{query_string}"
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            pre_sign.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        endpoint = f"{self._base_url}{endpoint_path}?{query_string}"
        request = Request(
            endpoint,
            method="GET",
            headers={
                "User-Agent": "project-oracle/phase8-account-check",
                "X-BAPI-API-KEY": self._api_key,
                "X-BAPI-TIMESTAMP": timestamp,
                "X-BAPI-RECV-WINDOW": str(self._recv_window),
                "X-BAPI-SIGN-TYPE": "2",
                "X-BAPI-SIGN": signature,
            },
        )

        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                body = response.read().decode("utf-8")
            payload = json.loads(body)
            ret_code = int(payload.get("retCode", -1))
            ret_msg = str(payload.get("retMsg", ""))

            if ret_code != 0:
                return ExchangeAccountConnectivityStatus(
                    provider="bybit",
                    enabled=True,
                    configured=True,
                    reachable=False,
                    detail=f"retCode={ret_code} retMsg={ret_msg}",
                    account_type=self._account_type,
                )

            return ExchangeAccountConnectivityStatus(
                provider="bybit",
                enabled=True,
                configured=True,
                reachable=True,
                detail="ok",
                account_type=self._account_type,
            )
        except HTTPError as exc:
            return ExchangeAccountConnectivityStatus(
                provider="bybit",
                enabled=True,
                configured=True,
                reachable=False,
                detail=f"http_error: {exc.code}",
                account_type=self._account_type,
            )
        except URLError as exc:
            return ExchangeAccountConnectivityStatus(
                provider="bybit",
                enabled=True,
                configured=True,
                reachable=False,
                detail=f"network_error: {str(exc.reason)}",
                account_type=self._account_type,
            )
        except Exception as exc:
            return ExchangeAccountConnectivityStatus(
                provider="bybit",
                enabled=True,
                configured=True,
                reachable=False,
                detail=f"error: {str(exc)}",
                account_type=self._account_type,
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
        api_key = os.getenv("ORACLE_EXCHANGE_API_KEY", "")
        api_secret = os.getenv("ORACLE_EXCHANGE_API_SECRET", "")
        recv_window = int(os.getenv("ORACLE_EXCHANGE_RECV_WINDOW_MS", "5000"))
        account_type = os.getenv("ORACLE_EXCHANGE_ACCOUNT_TYPE", "UNIFIED")
        return BybitExchangeAdapter(
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            api_key=api_key,
            api_secret=api_secret,
            recv_window=recv_window,
            account_type=account_type,
        )

    return UnsupportedExchangeAdapter(provider=provider or "unknown")
