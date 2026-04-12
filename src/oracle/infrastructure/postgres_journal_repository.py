from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from typing import Any

from oracle.infrastructure.retry import with_retry


class PostgresJournalRepository:
    def __init__(
        self,
        dsn: str,
        table_name: str = "trade_events",
        max_retries: int = 2,
        retry_delay_seconds: float = 0.2,
        fallback_file_path: str = "runtime-fallback/journal-events.jsonl",
    ) -> None:
        self._dsn = dsn
        self._table_name = table_name
        self._max_retries = max_retries
        self._retry_delay_seconds = retry_delay_seconds
        self._fallback_file_path = Path(fallback_file_path)

    def save_events(self, events: list[dict[str, Any]]) -> None:
        serialized_events = [self._serialize_event(event) for event in events]
        pending_events = self._read_fallback_events() + serialized_events

        try:
            with_retry(
                lambda: self._save_events_once(pending_events),
                max_retries=self._max_retries,
                delay_seconds=self._retry_delay_seconds,
            )
            self._clear_fallback()
        except Exception:
            self._write_fallback(serialized_events)

    def _save_events_once(self, events: list[dict[str, Any]]) -> None:
        try:
            import psycopg  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "psycopg package is required for PostgresJournalRepository"
            ) from exc

        with psycopg.connect(self._dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self._table_name} (
                        id BIGSERIAL PRIMARY KEY,
                        event_key TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        payload JSONB NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
                cursor.execute(
                    f"ALTER TABLE {self._table_name} ADD COLUMN IF NOT EXISTS event_key TEXT"
                )
                cursor.execute(
                    f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{self._table_name}_event_key ON {self._table_name} (event_key)"
                )
                for event in events:
                    cursor.execute(
                        f"INSERT INTO {self._table_name} (event_key, event_type, payload) VALUES (%s, %s, %s) ON CONFLICT (event_key) DO NOTHING",
                        (
                            event["event_key"],
                            event["event_type"],
                            json.dumps(asdict_safe(event["payload"])),
                        ),
                    )
            connection.commit()

    def _write_fallback(self, events: list[dict[str, Any]]) -> None:
        self._fallback_file_path.parent.mkdir(parents=True, exist_ok=True)
        with self._fallback_file_path.open("a", encoding="utf-8") as file_obj:
            for event in events:
                file_obj.write(json.dumps(event, ensure_ascii=True) + "\n")

    def _read_fallback_events(self) -> list[dict[str, Any]]:
        if not self._fallback_file_path.exists():
            return []

        events: list[dict[str, Any]] = []
        with self._fallback_file_path.open("r", encoding="utf-8") as file_obj:
            for line in file_obj:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if isinstance(row, dict):
                    event_type = str(row.get("event_type", "unknown"))
                    payload = asdict_safe(row.get("payload", {}))
                    event_key = str(row.get("event_key", self._build_event_key(event_type, payload)))
                    events.append(
                        {
                            "event_key": event_key,
                            "event_type": event_type,
                            "payload": payload,
                        }
                    )
        return events

    def _clear_fallback(self) -> None:
        if self._fallback_file_path.exists():
            self._fallback_file_path.unlink()

    def _serialize_event(self, event: dict[str, Any]) -> dict[str, Any]:
        event_type = str(event["event_type"])
        payload = asdict_safe(event["payload"])
        return {
            "event_key": self._build_event_key(event_type, payload),
            "event_type": event_type,
            "payload": payload,
        }

    def _build_event_key(self, event_type: str, payload: Any) -> str:
        canonical = json.dumps(
            {
                "event_type": event_type,
                "payload": payload,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def asdict_safe(payload: Any) -> Any:
    if hasattr(payload, "__dataclass_fields__"):
        return asdict(payload)
    return payload
