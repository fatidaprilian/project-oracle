from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

ALLOWED_REQUEST_STATUSES = {"pending", "approved", "rejected"}

PARAMETER_RULES: dict[str, tuple[float, float]] = {
    "min_confluence_score": (40.0, 95.0),
    "min_volume_threshold": (100.0, 1_000_000.0),
    "max_consecutive_losses": (1.0, 10.0),
}


@dataclass(frozen=True)
class TradeReviewItem:
    trade_index: int
    quality_score: float
    mae: float
    mfe: float
    close_reason: str


def select_worst_trades(events: list[dict[str, Any]], limit: int = 10) -> list[TradeReviewItem]:
    close_reasons: list[str] = []
    quality_items: list[TradeReviewItem] = []

    trade_index = 0
    for event in events:
        event_type = str(event.get("event_type", ""))
        payload = event.get("payload", {})

        if event_type == "position_closed":
            reason = payload.get("reason", "UNKNOWN") if isinstance(payload, dict) else "UNKNOWN"
            close_reasons.append(str(reason))

        if event_type == "trade_quality_assessed" and isinstance(payload, dict):
            close_reason = close_reasons[-1] if close_reasons else "UNKNOWN"
            quality_items.append(
                TradeReviewItem(
                    trade_index=trade_index,
                    quality_score=float(payload.get("quality_score", 0.0)),
                    mae=float(payload.get("mae", 0.0)),
                    mfe=float(payload.get("mfe", 0.0)),
                    close_reason=close_reason,
                )
            )
            trade_index += 1

    return sorted(quality_items, key=lambda item: item.quality_score)[:limit]


def build_ai_review_packet(
    events: list[dict[str, Any]],
    ai_provider: str,
    runtime_mode: str,
    exchange_env: str,
    limit: int = 10,
) -> dict[str, Any]:
    worst_trades = select_worst_trades(events, limit=limit)

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "provider": ai_provider,
        "runtime_mode": runtime_mode,
        "exchange_env": exchange_env,
        "prompt": (
            "Analyze the worst trade outcomes and propose parameter changes "
            "for confluence threshold, liquidity filter, and risk lock policy."
        ),
        "worst_trades": [
            {
                "trade_index": item.trade_index,
                "quality_score": item.quality_score,
                "mae": item.mae,
                "mfe": item.mfe,
                "close_reason": item.close_reason,
            }
            for item in worst_trades
        ],
    }


def write_ai_review_packet(output_dir: Path, packet: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{datetime.now(UTC).strftime('%G-W%V')}-ai-review.json"
    output_path = output_dir / file_name
    output_path.write_text(json.dumps(packet, indent=2, ensure_ascii=True), encoding="utf-8")
    return output_path


def validate_suggested_changes(suggested_changes: dict[str, float]) -> list[str]:
    violations: list[str] = []
    for parameter_name, parameter_value in suggested_changes.items():
        if parameter_name not in PARAMETER_RULES:
            violations.append(f"UNKNOWN_PARAMETER:{parameter_name}")
            continue
        minimum, maximum = PARAMETER_RULES[parameter_name]
        if not (minimum <= float(parameter_value) <= maximum):
            violations.append(
                f"OUT_OF_RANGE:{parameter_name}:{parameter_value}:allowed[{minimum},{maximum}]"
            )
    return violations


def build_parameter_change_request(
    generated_from: str,
    provider: str,
    suggested_changes: dict[str, float],
    status: str = "pending",
) -> dict[str, Any]:
    normalized_status = status.lower().strip()
    if normalized_status not in ALLOWED_REQUEST_STATUSES:
        normalized_status = "pending"

    violations = validate_suggested_changes(suggested_changes)
    is_valid = len(violations) == 0

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "generated_from": generated_from,
        "provider": provider,
        "status": normalized_status,
        "validation": {
            "is_valid": is_valid,
            "violations": violations,
        },
        "suggested_changes": suggested_changes,
    }


def append_parameter_change_request(registry_file: Path, request: dict[str, Any]) -> None:
    registry_file.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(request, ensure_ascii=True)
    with registry_file.open("a", encoding="utf-8") as file_obj:
        file_obj.write(line + "\n")


def summarize_parameter_change_registry(registry_file: Path) -> dict[str, Any]:
    if not registry_file.exists():
        return {
            "total": 0,
            "pending": 0,
            "approved": 0,
            "rejected": 0,
            "ready_to_promote": 0,
        }

    summary = {
        "total": 0,
        "pending": 0,
        "approved": 0,
        "rejected": 0,
        "ready_to_promote": 0,
    }
    with registry_file.open("r", encoding="utf-8") as file_obj:
        for line in file_obj:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                continue

            summary["total"] += 1
            status = str(record.get("status", "pending")).lower()
            if status in ("pending", "approved", "rejected"):
                summary[status] += 1

            validation = record.get("validation", {})
            is_valid = bool(validation.get("is_valid", False)) if isinstance(validation, dict) else False
            if status == "approved" and is_valid:
                summary["ready_to_promote"] += 1

    return summary
