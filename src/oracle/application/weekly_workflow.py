from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from oracle.application.replay_runner import run_replay
from oracle.application.strategy_intelligence import (
    append_parameter_change_request,
    build_ai_review_packet,
    build_parameter_change_request,
    promote_approved_requests,
    summarize_parameter_change_registry,
    write_ai_review_packet,
)
from oracle.application.weekly_report import write_weekly_report
from oracle.modules.sentiment_gate import StaticSentimentProvider


@dataclass
class WorkflowResult:
    success: bool
    ai_review_packet_path: Path | None = None
    weekly_report_path: Path | None = None
    governance_summary: dict[str, Any] | None = None
    promoted_config_path: Path | None = None
    error: str | None = None
    details: list[str] = field(default_factory=list)


def run_weekly_workflow(
    dataset_path: Path = Path("data/replay/sample_snapshots.jsonl"),
    ai_provider: str = "gemini",
    runtime_mode: str = "paper",
    exchange_env: str = "testnet",
    symbol: str = "",
    registry_file: Path = Path("registry/parameter_change_requests.jsonl"),
    ai_review_output_dir: Path = Path("reports/ai-review"),
    weekly_output_dir: Path = Path("reports/weekly"),
    strategy_config_output_dir: Path = Path("reports/strategy-configs"),
) -> WorkflowResult:
    """
    Run complete weekly workflow:
    1. Run replay and generate AI review packet
    2. Generate weekly report with governance summary
    3. Attempt to promote approved valid requests to strategy config
    """
    result = WorkflowResult(success=False)

    try:
        # Ensure directories exist
        ai_review_output_dir.mkdir(parents=True, exist_ok=True)
        weekly_output_dir.mkdir(parents=True, exist_ok=True)
        strategy_config_output_dir.mkdir(parents=True, exist_ok=True)
        registry_file.parent.mkdir(parents=True, exist_ok=True)

        # Step 1: Run replay and generate AI review packet
        target_symbol = symbol.strip()
        replay_label = f" for symbol={target_symbol}" if target_symbol else ""
        result.details.append(f"Running replay{replay_label}...")
        events = run_replay(
            dataset_path,
            StaticSentimentProvider(),
            symbol=target_symbol,
        )
        result.details.append(f"Replay complete: {len(events)} events")

        result.details.append("Building AI review packet...")
        packet = build_ai_review_packet(
            events=events,
            ai_provider=ai_provider,
            runtime_mode=runtime_mode,
            exchange_env=exchange_env,
            limit=10,
        )

        result.details.append("Writing AI review packet...")
        result.ai_review_packet_path = write_ai_review_packet(
            ai_review_output_dir, packet)
        result.details.append(
            f"AI review packet written to {result.ai_review_packet_path}")

        # Record the AI packet as a pending request
        result.details.append("Recording parameter change request...")
        request = build_parameter_change_request(
            generated_from=str(result.ai_review_packet_path),
            provider=ai_provider,
            status="pending",
            symbol=target_symbol,
            suggested_changes={
                "min_confluence_score": 62.0,
                "min_volume_threshold": 850.0,
                "max_consecutive_losses": 3.0,
            },
        )
        append_parameter_change_request(registry_file, request)
        result.details.append("Parameter change request recorded")

        # Step 2: Generate weekly report with governance summary
        result.details.append("Summarizing governance registry...")
        result.governance_summary = summarize_parameter_change_registry(
            registry_file)
        result.details.append(
            f"Governance summary: total={result.governance_summary.get('total')}, "
            f"approved={result.governance_summary.get('approved')}, "
            f"ready_to_promote={result.governance_summary.get('ready_to_promote')}"
        )

        result.details.append("Writing weekly report...")
        result.weekly_report_path = write_weekly_report(
            weekly_output_dir,
            events,
            governance_summary=result.governance_summary,
        )
        result.details.append(
            f"Weekly report written to {result.weekly_report_path}")

        # Step 3: Attempt to promote approved valid requests
        result.details.append("Attempting to promote approved requests...")
        promoted_path = promote_approved_requests(
            registry_file, strategy_config_output_dir)
        if promoted_path:
            result.promoted_config_path = promoted_path
            result.details.append(
                f"Strategy config promoted to {promoted_path}")
        else:
            result.details.append(
                "No approved valid requests to promote (expected: decisions pending)")

        result.success = True

    except Exception as e:
        result.error = f"Workflow failed: {type(e).__name__}: {str(e)}"
        result.details.append(result.error)

    return result
