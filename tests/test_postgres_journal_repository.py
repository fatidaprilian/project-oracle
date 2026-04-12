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


if __name__ == "__main__":
    unittest.main()
