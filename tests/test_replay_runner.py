from __future__ import annotations

import json
import unittest
from pathlib import Path

from oracle.application.replay_runner import load_replay_symbols, run_replay
from oracle.modules.sentiment_gate import StaticSentimentProvider


class ReplayRunnerTest(unittest.TestCase):
    def test_should_emit_events_when_dataset_is_loaded(self) -> None:
        dataset_path = Path("data/replay/sample_snapshots.jsonl")

        events = run_replay(dataset_path, StaticSentimentProvider())

        self.assertGreater(len(events), 0)
        self.assertEqual(events[0]["event_type"], "structure_evaluated")

    def test_should_handle_multi_symbol_dataset_without_error(self) -> None:
        dataset_path = Path("data/replay/sample_snapshots.jsonl")

        symbols = load_replay_symbols(dataset_path)
        with dataset_path.open("r", encoding="utf-8") as file_obj:
            records = [json.loads(line) for line in file_obj if line.strip()]

        self.assertGreater(len(symbols), 1)
        self.assertEqual(sorted({record["symbol"] for record in records}), symbols)

        events = run_replay(dataset_path, StaticSentimentProvider())

        self.assertGreater(len(events), 0)
        self.assertIn("candidate_rejected", {event["event_type"] for event in events})

    def test_should_filter_replay_events_by_symbol_when_symbol_is_provided(self) -> None:
        dataset_path = Path("data/replay/sample_snapshots.jsonl")

        events = run_replay(
            dataset_path,
            StaticSentimentProvider(),
            symbol="BTCUSDT",
        )

        self.assertGreater(len(events), 0)
        for event in events:
            payload = event.get("payload", {})
            if isinstance(payload, dict) and "symbol" in payload:
                self.assertEqual(payload["symbol"], "BTCUSDT")


if __name__ == "__main__":
    unittest.main()
