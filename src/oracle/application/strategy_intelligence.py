from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any


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


def append_parameter_change_request(registry_file: Path, request: dict[str, Any]) -> None:
    registry_file.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(request, ensure_ascii=True)
    with registry_file.open("a", encoding="utf-8") as file_obj:
        file_obj.write(line + "\n")
