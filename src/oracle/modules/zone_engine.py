from __future__ import annotations

from oracle.domain.models import MarketRegime, MarketSnapshot, StructureSignal, ZoneSignal, ZoneType


def detect_zone(snapshot: MarketSnapshot, structure: StructureSignal) -> ZoneSignal:
    window_high = max(snapshot.highs[-5:]) if len(snapshot.highs) >= 5 else max(snapshot.highs)
    window_low = min(snapshot.lows[-5:]) if len(snapshot.lows) >= 5 else min(snapshot.lows)

    if structure.market_regime == MarketRegime.UPTREND:
        return ZoneSignal(
            zone_low=window_low,
            zone_high=(window_low + window_high) / 2,
            zone_type=ZoneType.DEMAND,
            freshness_score=0.75,
        )

    return ZoneSignal(
        zone_low=(window_low + window_high) / 2,
        zone_high=window_high,
        zone_type=ZoneType.SUPPLY,
        freshness_score=0.75,
    )
