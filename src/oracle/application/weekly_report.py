from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any


def build_weekly_report(
    events: list[dict[str, Any]],
    governance_summary: dict[str, int] | None = None,
) -> str:
    event_counter = Counter(event["event_type"] for event in events)

    rejection_reasons: list[str] = []
    close_reasons: list[str] = []
    quality_scores: list[float] = []
    mae_values: list[float] = []
    mfe_values: list[float] = []
    for event in events:
        event_type = event.get("event_type")
        payload = event.get("payload", {})
        if event_type == "candidate_rejected":
            reason = payload.get("reason") if isinstance(payload, dict) else payload
            if isinstance(reason, list):
                rejection_reasons.extend(str(item) for item in reason)
            elif reason is not None:
                rejection_reasons.append(str(reason))
        if event_type == "position_closed" and isinstance(payload, dict):
            close_reasons.append(str(payload.get("reason", "UNKNOWN")))
        if event_type == "trade_quality_assessed" and isinstance(payload, dict):
            quality_scores.append(float(payload.get("quality_score", 0.0)))
            mae_values.append(float(payload.get("mae", 0.0)))
            mfe_values.append(float(payload.get("mfe", 0.0)))

    rejection_counter = Counter(rejection_reasons)
    close_counter = Counter(close_reasons)

    lines = [
        "# Weekly Trading Report",
        "",
        f"generated_at: {datetime.now(UTC).isoformat()}",
        "",
        "## Event Volume",
    ]
    lines.extend(f"- {name}: {count}" for name, count in sorted(event_counter.items()))

    lines.append("")
    lines.append("## Top Rejection Reasons")
    if rejection_counter:
        lines.extend(f"- {reason}: {count}" for reason, count in rejection_counter.most_common(10))
    else:
        lines.append("- none")

    lines.append("")
    lines.append("## Close Reasons")
    if close_counter:
        lines.extend(f"- {reason}: {count}" for reason, count in close_counter.most_common(10))
    else:
        lines.append("- none")

    lines.append("")
    lines.append("## Trade Quality")
    if quality_scores:
        lines.append(f"- avg_quality_score: {round(mean(quality_scores), 2)}")
        lines.append(f"- avg_mae: {round(mean(mae_values), 6)}")
        lines.append(f"- avg_mfe: {round(mean(mfe_values), 6)}")
    else:
        lines.append("- none")

    if governance_summary is not None:
        lines.append("")
        lines.append("## Parameter Governance")
        lines.append(f"- total_requests: {governance_summary.get('total', 0)}")
        lines.append(f"- pending: {governance_summary.get('pending', 0)}")
        lines.append(f"- approved: {governance_summary.get('approved', 0)}")
        lines.append(f"- rejected: {governance_summary.get('rejected', 0)}")
        lines.append(f"- ready_to_promote: {governance_summary.get('ready_to_promote', 0)}")

    return "\n".join(lines) + "\n"


def write_weekly_report(
    output_dir: Path,
    events: list[dict[str, Any]],
    governance_summary: dict[str, int] | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{datetime.now(UTC).strftime('%G-W%V')}.md"
    report_path = output_dir / file_name
    report_path.write_text(build_weekly_report(events, governance_summary=governance_summary), encoding="utf-8")
    return report_path
