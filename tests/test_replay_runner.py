from __future__ import annotations

import unittest
from pathlib import Path

from oracle.application.replay_runner import run_replay
from oracle.modules.sentiment_gate import StaticSentimentProvider


class ReplayRunnerTest(unittest.TestCase):
    def test_should_emit_events_when_dataset_is_loaded(self) -> None:
        dataset_path = Path("data/replay/sample_snapshots.jsonl")

        events = run_replay(dataset_path, StaticSentimentProvider())

        self.assertGreater(len(events), 0)
        self.assertEqual(events[0]["event_type"], "structure_evaluated")


if __name__ == "__main__":
    unittest.main()
