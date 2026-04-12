from __future__ import annotations

from dataclasses import dataclass

from oracle.domain.models import MarketSnapshot


@dataclass
class RiskConfig:
    max_daily_loss_r: float = 3.0
    max_consecutive_losses: int = 3
    min_volume_threshold: float = 500.0


@dataclass
class RiskState:
    cumulative_loss_r: float = 0.0
    consecutive_losses: int = 0
    is_locked: bool = False
    lock_reason: str = ""


class RiskGuard:
    def __init__(self, config: RiskConfig, state: RiskState | None = None) -> None:
        self._config = config
        self._state = state or RiskState()

    @property
    def state(self) -> RiskState:
        return self._state

    def pre_trade_check(self, snapshot: MarketSnapshot) -> tuple[bool, str]:
        if self._state.is_locked:
            return False, self._state.lock_reason or "CIRCUIT_BREAKER_LOCKED"

        if snapshot.volume < self._config.min_volume_threshold:
            return False, "LOW_LIQUIDITY"

        return True, "OK"

    def register_closed_trade(self, realized_r_multiple: float) -> None:
        if realized_r_multiple < 0:
            self._state.cumulative_loss_r += abs(realized_r_multiple)
            self._state.consecutive_losses += 1
        else:
            self._state.consecutive_losses = 0

        if self._state.cumulative_loss_r >= self._config.max_daily_loss_r:
            self._state.is_locked = True
            self._state.lock_reason = "DAILY_LOSS_LIMIT"

        if self._state.consecutive_losses >= self._config.max_consecutive_losses:
            self._state.is_locked = True
            self._state.lock_reason = "CONSECUTIVE_LOSS_LIMIT"

    def reset_daily_state(self) -> None:
        self._state.cumulative_loss_r = 0.0
        self._state.consecutive_losses = 0
        self._state.is_locked = False
        self._state.lock_reason = ""
