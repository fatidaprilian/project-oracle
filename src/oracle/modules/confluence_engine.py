from __future__ import annotations

from oracle.domain.models import ConfluenceSignal, MarketSnapshot, ZoneSignal


def evaluate_confluence(snapshot: MarketSnapshot, zone: ZoneSignal) -> ConfluenceSignal:
    swing_high = max(snapshot.highs[-10:]) if len(snapshot.highs) >= 10 else max(snapshot.highs)
    swing_low = min(snapshot.lows[-10:]) if len(snapshot.lows) >= 10 else min(snapshot.lows)
    fib_618_price = swing_high - (swing_high - swing_low) * 0.618

    cluster_price = (fib_618_price + zone.zone_low + zone.zone_high) / 3
    distance = abs(snapshot.current_price - cluster_price)
    normalized_distance = min(distance / max(snapshot.current_price, 1e-9), 1.0)
    score = round((1.0 - normalized_distance) * 100, 2)

    return ConfluenceSignal(
        confluence_score=score,
        fib_618_price=fib_618_price,
        cluster_price=cluster_price,
        is_valid=score >= 60,
    )
