from __future__ import annotations

from pathlib import Path

from oracle.application.replay_runner import run_replay
from oracle.runtime import build_runtime_components


def main() -> None:
    dataset_path = Path("data/replay/sample_snapshots.jsonl")
    runtime = build_runtime_components()
    events = run_replay(dataset_path, runtime.sentiment_provider)
    runtime.risk_state_store and runtime.risk_state_store.save_state(runtime.risk_guard.state)
    print(f"replay_events={len(events)}")
    for event in events[-10:]:
        print(event)


if __name__ == "__main__":
    main()
