from __future__ import annotations

from oracle.domain.models import MarketRegime, MarketSnapshot, StructureSignal


def evaluate_structure(snapshot: MarketSnapshot) -> StructureSignal:
    if len(snapshot.closes) < 3:
        return StructureSignal(
            market_regime=MarketRegime.CHOP,
            structure_strength=0.0,
            is_tradeable=False,
        )

    if snapshot.closes[-1] > snapshot.closes[-2] > snapshot.closes[-3]:
        return StructureSignal(
            market_regime=MarketRegime.UPTREND,
            structure_strength=0.8,
            is_tradeable=True,
        )

    if snapshot.closes[-1] < snapshot.closes[-2] < snapshot.closes[-3]:
        return StructureSignal(
            market_regime=MarketRegime.DOWNTREND,
            structure_strength=0.8,
            is_tradeable=True,
        )

    return StructureSignal(
        market_regime=MarketRegime.CHOP,
        structure_strength=0.2,
        is_tradeable=False,
    )
