from __future__ import annotations

from dataclasses import dataclass

from oracle.domain.models import MarketSnapshot, PositionState


@dataclass(frozen=True)
class TradeQualityMetrics:
    mae: float
    mfe: float
    quality_score: float


def evaluate_trade_quality(snapshot: MarketSnapshot, position: PositionState) -> TradeQualityMetrics:
    lowest_price = min(snapshot.lows) if snapshot.lows else snapshot.current_price
    highest_price = max(snapshot.highs) if snapshot.highs else snapshot.current_price

    # Long-oriented metrics for phase-1 pipeline.
    mae = max(position.entry_price - lowest_price, 0.0)
    mfe = max(highest_price - position.entry_price, 0.0)

    denominator = mae + mfe
    if denominator <= 0:
        quality_score = 50.0
    else:
        quality_score = round((mfe / denominator) * 100.0, 2)

    return TradeQualityMetrics(mae=round(mae, 6), mfe=round(mfe, 6), quality_score=quality_score)
