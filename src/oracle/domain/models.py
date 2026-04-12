from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class MarketRegime(str, Enum):
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    CHOP = "chop"


class ZoneType(str, Enum):
    DEMAND = "demand"
    SUPPLY = "supply"


@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    timeframe: str
    closes: List[float]
    highs: List[float]
    lows: List[float]
    current_price: float
    volume: float


@dataclass(frozen=True)
class StructureSignal:
    market_regime: MarketRegime
    structure_strength: float
    is_tradeable: bool


@dataclass(frozen=True)
class ZoneSignal:
    zone_low: float
    zone_high: float
    zone_type: ZoneType
    freshness_score: float


@dataclass(frozen=True)
class ConfluenceSignal:
    confluence_score: float
    fib_618_price: float
    cluster_price: float
    is_valid: bool


@dataclass(frozen=True)
class SentimentSignal:
    sentiment_bias: str
    event_risk_level: str
    shield_status: bool


@dataclass
class EntryPlan:
    should_place_order: bool
    entry_price: float
    stop_loss: float
    take_profit_primary: float
    take_profit_secondary: float
    reason_codes: List[str] = field(default_factory=list)


@dataclass
class PositionState:
    symbol: str
    side: str
    entry_price: float
    stop_loss: float
    take_profit_primary: float
    take_profit_secondary: float
    is_break_even_armed: bool = False
    is_open: bool = True


@dataclass(frozen=True)
class ExitDecision:
    should_close: bool
    exit_reason: str
    updated_stop_loss: float
