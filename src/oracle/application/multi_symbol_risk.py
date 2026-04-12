from __future__ import annotations

from dataclasses import dataclass, field

from oracle.application.risk_controls import RiskConfig, RiskGuard, RiskState
from oracle.domain.models import MarketSnapshot


@dataclass
class SymbolRiskProfile:
    symbol: str
    config: RiskConfig
    guard: RiskGuard = field(init=False)

    def __post_init__(self) -> None:
        self.guard = RiskGuard(self.config)

    @property
    def state(self) -> RiskState:
        return self.guard.state


class MultiSymbolRiskManager:
    def __init__(self) -> None:
        self._profiles: dict[str, SymbolRiskProfile] = {}

    def register_symbol(
        self,
        symbol: str,
        config: RiskConfig | None = None,
    ) -> SymbolRiskProfile:
        if symbol not in self._profiles:
            self._profiles[symbol] = SymbolRiskProfile(
                symbol=symbol,
                config=config or RiskConfig(),
            )
        return self._profiles[symbol]

    def get_profile(self, symbol: str) -> SymbolRiskProfile:
        if symbol not in self._profiles:
            return self.register_symbol(symbol)
        return self._profiles[symbol]

    def check_trade_allowed(self, snapshot: MarketSnapshot) -> tuple[bool, str]:
        profile = self.get_profile(snapshot.symbol)
        return profile.guard.pre_trade_check(snapshot)

    def record_trade_result(
        self,
        symbol: str,
        realized_r_multiple: float,
    ) -> None:
        profile = self.get_profile(symbol)
        profile.guard.register_closed_trade(realized_r_multiple)

    def reset_symbol_daily(self, symbol: str) -> None:
        profile = self.get_profile(symbol)
        profile.guard.reset_daily_state()

    def reset_all_daily(self) -> None:
        for profile in self._profiles.values():
            profile.guard.reset_daily_state()

    def get_all_profiles(self) -> list[SymbolRiskProfile]:
        return list(self._profiles.values())

    def apply_config_bulk(
        self,
        configs: dict[str, RiskConfig],
    ) -> None:
        for symbol, config in configs.items():
            profile = self.get_profile(symbol)
            profile.config = config
            profile.guard._config = config
