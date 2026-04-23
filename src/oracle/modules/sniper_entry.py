from __future__ import annotations

from oracle.domain.models import ConfluenceSignal, EntryPlan, MarketSnapshot, PullbackSignal, SentimentSignal, ZoneSignal


def build_entry_plan(
    snapshot: MarketSnapshot,
    zone: ZoneSignal,
    confluence: ConfluenceSignal,
    sentiment: SentimentSignal,
    pullback: PullbackSignal | None = None,
) -> EntryPlan:
    reason_codes: list[str] = []

    if sentiment.shield_status:
        reason_codes.append("NEWS_SHIELD_ACTIVE")
        return EntryPlan(False, 0.0, 0.0, 0.0, 0.0, reason_codes)

    if not confluence.is_valid:
        reason_codes.append("LOW_CONFLUENCE")
        return EntryPlan(False, 0.0, 0.0, 0.0, 0.0, reason_codes)

    if pullback is not None and not pullback.is_valid:
        reason_codes.append("PULLBACK_CONFLUENCE_FAIL")
        reason_codes.extend(pullback.reason_codes)
        return EntryPlan(False, 0.0, 0.0, 0.0, 0.0, reason_codes)

    # Simulate sweep-reclaim: current price should be back inside zone after touching zone edge.
    is_inside_zone = zone.zone_low <= snapshot.current_price <= zone.zone_high
    if not is_inside_zone:
        reason_codes.append("SWEEP_NOT_CONFIRMED")
        return EntryPlan(False, 0.0, 0.0, 0.0, 0.0, reason_codes)

    entry_price = confluence.cluster_price
    risk_distance = max(abs(entry_price - zone.zone_low), entry_price * 0.002)
    stop_loss = entry_price - risk_distance
    take_profit_primary = entry_price + risk_distance * 1.272
    take_profit_secondary = entry_price + risk_distance * 1.618

    reason_codes.append("ENTRY_LIMIT_READY")
    if pullback is not None and pullback.strategy_name != "NONE":
        reason_codes.append(f"STRATEGY_{pullback.strategy_name}")

    return EntryPlan(
        should_place_order=True,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit_primary=take_profit_primary,
        take_profit_secondary=take_profit_secondary,
        reason_codes=reason_codes,
    )
