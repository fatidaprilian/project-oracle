from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnomalyLaneDecision:
    lane: str
    reason: str
    discovery_score: float


def classify_volume_anomaly(
    *,
    close_price: float,
    volume_ratio: float,
    change_pct: float,
) -> AnomalyLaneDecision:
    if close_price < 50:
        return AnomalyLaneDecision(
            lane="RADAR_ONLY",
            reason="LOW_PRICE_LIQUIDITY_RISK",
            discovery_score=_score_anomaly(volume_ratio, change_pct) * 0.5,
        )

    if change_pct > 15:
        return AnomalyLaneDecision(
            lane="EXTENDED_RISK",
            reason="PRICE_ALREADY_EXTENDED",
            discovery_score=_score_anomaly(volume_ratio, change_pct) * 0.7,
        )

    if volume_ratio >= 5 and change_pct >= 1.5:
        return AnomalyLaneDecision(
            lane="MOMENTUM_WATCH",
            reason="VOLUME_EXPANSION_WITH_PRICE_CONFIRMATION",
            discovery_score=_score_anomaly(volume_ratio, change_pct),
        )

    return AnomalyLaneDecision(
        lane="RADAR_ONLY",
        reason="VOLUME_ANOMALY_NEEDS_PRICE_CONFIRMATION",
        discovery_score=_score_anomaly(volume_ratio, change_pct) * 0.75,
    )


def _score_anomaly(volume_ratio: float, change_pct: float) -> float:
    ratio_component = min(max(volume_ratio, 0.0), 20.0) * 3.5
    change_component = min(max(change_pct, 0.0), 15.0) * 2.0
    return round(min(ratio_component + change_component, 100.0), 2)
