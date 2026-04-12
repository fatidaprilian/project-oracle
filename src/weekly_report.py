from __future__ import annotations

from pathlib import Path

from oracle.application.replay_runner import run_replay
from oracle.application.strategy_intelligence import summarize_parameter_change_registry
from oracle.application.weekly_report import write_weekly_report
from oracle.modules.sentiment_gate import StaticSentimentProvider


def main() -> None:
    dataset_path = Path("data/replay/sample_snapshots.jsonl")
    events = run_replay(dataset_path, StaticSentimentProvider())
    governance_summary = summarize_parameter_change_registry(
        Path("registry/parameter_change_requests.jsonl")
    )
    report_path = write_weekly_report(
        Path("reports/weekly"),
        events,
        governance_summary=governance_summary,
    )
    print(f"weekly_report={report_path}")


if __name__ == "__main__":
    main()
