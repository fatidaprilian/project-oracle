from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from oracle.infrastructure.postgres_journal_repository import PostgresJournalRepository


class PostgresJournalRepositoryTest(unittest.TestCase):
    def test_should_write_fallback_file_when_persistence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fallback_file = Path(temp_dir) / "events.jsonl"
            repository = PostgresJournalRepository(
                dsn="postgresql://invalid",
                fallback_file_path=str(fallback_file),
                max_retries=0,
                retry_delay_seconds=0.0,
            )

            repository.save_events([
                {"event_type": "candidate_rejected", "payload": {"reason": "LOW_LIQUIDITY"}}
            ])

            self.assertTrue(fallback_file.exists())
            content = fallback_file.read_text(encoding="utf-8")
            self.assertIn("candidate_rejected", content)

    def test_should_build_same_event_key_for_same_payload_order_independent(self) -> None:
        repository = PostgresJournalRepository(dsn="postgresql://unused", max_retries=0)

        key_a = repository._build_event_key("candidate_rejected", {"a": 1, "b": 2})
        key_b = repository._build_event_key("candidate_rejected", {"b": 2, "a": 1})

        self.assertEqual(key_a, key_b)

    def test_should_replay_and_clear_fallback_when_sink_recovers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fallback_file = Path(temp_dir) / "events.jsonl"
            fallback_file.write_text(
                '{"event_type":"candidate_rejected","payload":{"reason":"LOW_LIQUIDITY"}}\n',
                encoding="utf-8",
            )

            repository = PostgresJournalRepository(
                dsn="postgresql://unused",
                fallback_file_path=str(fallback_file),
                max_retries=0,
                retry_delay_seconds=0.0,
            )

            captured_events: list[dict[str, object]] = []
            repository._save_events_once = lambda events: captured_events.extend(events)  # type: ignore[method-assign]

            repository.save_events([
                {"event_type": "position_closed", "payload": {"reason": "FIB_EXTENSION_TP_HIT"}}
            ])

            self.assertEqual(len(captured_events), 2)
            self.assertFalse(fallback_file.exists())


if __name__ == "__main__":
    unittest.main()
