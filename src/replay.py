from __future__ import annotations

from pathlib import Path

from oracle.application.replay_runner import run_replay
from oracle.modules.sentiment_gate import StaticSentimentProvider


def main() -> None:
    dataset_path = Path("data/replay/sample_snapshots.jsonl")
    events = run_replay(dataset_path, StaticSentimentProvider())
    print(f"replay_events={len(events)}")
    for event in events[-10:]:
        print(event)


if __name__ == "__main__":
    main()
