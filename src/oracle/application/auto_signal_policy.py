from __future__ import annotations

import os
from typing import Any


def minimum_auto_signal_confluence() -> float:
    raw_threshold = os.getenv("ORACLE_AUTO_SIGNAL_MIN_CONFLUENCE", "80")
    try:
        threshold = float(raw_threshold)
    except (TypeError, ValueError):
        threshold = 80.0
    return max(60.0, min(threshold, 100.0))


def is_conservative_entry_candidate(
    quant_results: dict[str, Any],
) -> tuple[bool, list[str]]:
    structure = quant_results["structure"]
    confluence = quant_results["confluence"]
    pullback = quant_results["pullback"]
    entry_plan = quant_results["entry_plan"]
    minimum_confluence = minimum_auto_signal_confluence()

    rejection_reasons: list[str] = []

    if not structure.is_tradeable:
        rejection_reasons.append("STRUCTURE_NOT_TRADEABLE")

    if structure.market_regime.value != "uptrend":
        rejection_reasons.append("REGIME_NOT_UPTREND")

    if confluence.confluence_score < minimum_confluence:
        rejection_reasons.append(f"CONFLUENCE_BELOW_{minimum_confluence:.0f}")

    if not pullback.is_valid:
        rejection_reasons.append("PULLBACK_NOT_CONFIRMED")

    if not entry_plan.should_place_order:
        rejection_reasons.append("ENTRY_PLAN_REJECTED")

    return not rejection_reasons, rejection_reasons
