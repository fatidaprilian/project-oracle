from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any
import uuid

ALLOWED_REQUEST_STATUSES = {"pending", "approved", "rejected"}

# Global parameter rules (used as defaults for all symbols)
DEFAULT_PARAMETER_RULES: dict[str, tuple[float, float]] = {
    "min_confluence_score": (40.0, 95.0),
    "min_volume_threshold": (100.0, 1_000_000.0),
    "max_consecutive_losses": (1.0, 10.0),
}

# Per-symbol parameter rules (overrides defaults)
# Example: {"BTCUSDT": {"min_confluence_score": (45.0, 90.0)}, ...}
SYMBOL_PARAMETER_RULES: dict[str, dict[str, tuple[float, float]]] = {}

# Legacy compatibility
PARAMETER_RULES = DEFAULT_PARAMETER_RULES


def get_parameter_rules(symbol: str = "") -> dict[str, tuple[float, float]]:
    if symbol and symbol in SYMBOL_PARAMETER_RULES:
        rules = DEFAULT_PARAMETER_RULES.copy()
        rules.update(SYMBOL_PARAMETER_RULES[symbol])
        return rules
    return DEFAULT_PARAMETER_RULES.copy()


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
            reason = payload.get("reason", "UNKNOWN") if isinstance(
                payload, dict) else "UNKNOWN"
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
    output_path.write_text(json.dumps(
        packet, indent=2, ensure_ascii=True), encoding="utf-8")
    return output_path


def validate_suggested_changes(
    suggested_changes: dict[str, float],
    symbol: str = "",
) -> list[str]:
    violations: list[str] = []
    parameter_rules = get_parameter_rules(symbol)
    for parameter_name, parameter_value in suggested_changes.items():
        if parameter_name not in parameter_rules:
            violations.append(f"UNKNOWN_PARAMETER:{parameter_name}")
            continue
        minimum, maximum = parameter_rules[parameter_name]
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
    symbol: str = "",
) -> dict[str, Any]:
    normalized_status = status.lower().strip()
    if normalized_status not in ALLOWED_REQUEST_STATUSES:
        normalized_status = "pending"

    violations = validate_suggested_changes(suggested_changes, symbol=symbol)
    is_valid = len(violations) == 0

    request = {
        "request_id": str(uuid.uuid4()),
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
    if symbol:
        request["symbol"] = symbol
    return request


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
            is_valid = bool(validation.get("is_valid", False)
                            ) if isinstance(validation, dict) else False
            if status == "approved" and is_valid:
                summary["ready_to_promote"] += 1

    return summary


def load_parameter_change_requests(registry_file: Path) -> list[dict[str, Any]]:
    if not registry_file.exists():
        return []

    records: list[dict[str, Any]] = []
    with registry_file.open("r", encoding="utf-8") as file_obj:
        for line in file_obj:
            line = line.strip()
            if not line:
                continue
            parsed = json.loads(line)
            if isinstance(parsed, dict):
                records.append(parsed)
    return records


def write_parameter_change_requests(registry_file: Path, records: list[dict[str, Any]]) -> None:
    registry_file.parent.mkdir(parents=True, exist_ok=True)
    with registry_file.open("w", encoding="utf-8") as file_obj:
        for record in records:
            file_obj.write(json.dumps(record, ensure_ascii=True) + "\n")


def update_request_status_by_id(
    registry_file: Path,
    request_id: str,
    status: str,
) -> bool:
    normalized_status = status.lower().strip()
    if normalized_status not in ALLOWED_REQUEST_STATUSES:
        return False

    records = load_parameter_change_requests(registry_file)
    updated = False
    for record in records:
        if str(record.get("request_id", "")) == request_id:
            record["status"] = normalized_status
            record["status_updated_at"] = datetime.now(UTC).isoformat()
            updated = True
            break

    if updated:
        write_parameter_change_requests(registry_file, records)
    return updated


def promote_approved_requests(
    registry_file: Path,
    output_dir: Path,
) -> Path | None:
    records = load_parameter_change_requests(registry_file)
    promotable: list[dict[str, Any]] = []
    for record in records:
        status = str(record.get("status", "pending")).lower()
        validation = record.get("validation", {})
        is_valid = bool(validation.get("is_valid", False)
                        ) if isinstance(validation, dict) else False
        already_promoted = bool(record.get("promoted", False))
        if status == "approved" and is_valid and not already_promoted:
            promotable.append(record)

    if not promotable:
        return None

    merged_changes: dict[str, float] = {}
    promoted_ids: list[str] = []
    for record in promotable:
        changes = record.get("suggested_changes", {})
        if isinstance(changes, dict):
            for parameter_name, parameter_value in changes.items():
                merged_changes[str(parameter_name)] = float(parameter_value)
        promoted_ids.append(str(record.get("request_id", "")))

    hash_input = json.dumps(
        {"request_ids": promoted_ids, "changes": merged_changes}, sort_keys=True)
    version_suffix = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:8]
    version = f"strategy-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{version_suffix}"

    candidate_config = {
        "version": version,
        "created_at": datetime.now(UTC).isoformat(),
        "source_request_ids": promoted_ids,
        "parameters": merged_changes,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{version}.json"
    output_path.write_text(json.dumps(
        candidate_config, indent=2, ensure_ascii=True), encoding="utf-8")

    for record in records:
        request_id = str(record.get("request_id", ""))
        if request_id in promoted_ids:
            record["promoted"] = True
            record["promoted_at"] = datetime.now(UTC).isoformat()
            record["promoted_config"] = str(output_path)

    write_parameter_change_requests(registry_file, records)
    return output_path
