from __future__ import annotations


def normalize_bias(raw_bias: object) -> str:
    return str(raw_bias or "IGNORE").strip().upper()


def safe_int(raw_value: object) -> int | None:
    try:
        return int(round(float(raw_value)))
    except (TypeError, ValueError):
        return None


def default_duration_window(
    confluence_score: float,
    has_quant_entry_plan: bool,
) -> tuple[int, int]:
    if has_quant_entry_plan and confluence_score >= 80:
        return 3, 5
    if has_quant_entry_plan and confluence_score >= 65:
        return 4, 7
    if confluence_score >= 60:
        return 5, 8
    return 5, 10


def normalize_estimated_duration_window(
    raw_min_days: object,
    raw_max_days: object,
    bias: object,
    confluence_score: float,
    has_quant_entry_plan: bool,
) -> tuple[int | None, int | None]:
    normalized_bias = normalize_bias(bias)
    if normalized_bias not in {"BUY", "SELL"}:
        return None, None

    normalized_min_days = safe_int(raw_min_days)
    normalized_max_days = safe_int(raw_max_days)

    if (
        normalized_min_days is None
        or normalized_max_days is None
        or normalized_min_days <= 0
        or normalized_max_days <= 0
    ):
        normalized_min_days, normalized_max_days = default_duration_window(
            confluence_score=confluence_score,
            has_quant_entry_plan=has_quant_entry_plan,
        )

    normalized_min_days = max(2, min(normalized_min_days, 15))
    normalized_max_days = max(2, min(normalized_max_days, 15))

    if normalized_max_days < normalized_min_days:
        normalized_max_days = normalized_min_days

    return normalized_min_days, normalized_max_days


def format_bias_label(bias: str) -> str:
    if bias == "BUY":
        return "BELI"
    if bias == "SELL":
        return "JUAL"
    return "ABAIKAN"
