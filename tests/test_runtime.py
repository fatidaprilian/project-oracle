from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from oracle.infrastructure.journal import InMemoryJournal
from oracle.runtime import build_runtime_settings


class RuntimeBootstrapTest(unittest.TestCase):
    def test_should_read_disabled_runtime_flags_by_default(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = build_runtime_settings()

        self.assertFalse(settings.enable_postgres_persistence)
        self.assertFalse(settings.enable_redis_risk_state)
        self.assertEqual(settings.postgres_dsn, "")
        self.assertEqual(settings.redis_url, "")

    def test_should_flush_events_to_sink_when_present(self) -> None:
        captured_events: list[dict[str, object]] = []

        class _CaptureSink:
            def save_events(self, events: list[dict[str, object]]) -> None:
                captured_events.extend(events)

        journal = InMemoryJournal(_CaptureSink())
        journal.record("candidate_rejected", {"reason": "LOW_LIQUIDITY"})
        journal.flush()

        self.assertEqual(len(captured_events), 1)
        self.assertEqual(captured_events[0]["event_type"], "candidate_rejected")


if __name__ == "__main__":
    unittest.main()
