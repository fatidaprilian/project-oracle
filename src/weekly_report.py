from __future__ import annotations

from pathlib import Path

from oracle.application.replay_runner import run_replay
from oracle.application.weekly_report import write_weekly_report
from oracle.modules.sentiment_gate import StaticSentimentProvider


def main() -> None:
    dataset_path = Path("data/replay/sample_snapshots.jsonl")
    events = run_replay(dataset_path, StaticSentimentProvider())
    report_path = write_weekly_report(Path("reports/weekly"), events)
    print(f"weekly_report={report_path}")


if __name__ == "__main__":
    main()
