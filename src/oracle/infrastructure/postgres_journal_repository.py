from __future__ import annotations

from dataclasses import asdict
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
        try:
            with_retry(
                lambda: self._save_events_once(events),
                max_retries=self._max_retries,
                delay_seconds=self._retry_delay_seconds,
            )
        except Exception:
            self._write_fallback(events)

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
                        event_type TEXT NOT NULL,
                        payload JSONB NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
                for event in events:
                    cursor.execute(
                        f"INSERT INTO {self._table_name} (event_type, payload) VALUES (%s, %s)",
                        (event["event_type"], json.dumps(asdict_safe(event["payload"]))),
                    )
            connection.commit()

    def _write_fallback(self, events: list[dict[str, Any]]) -> None:
        self._fallback_file_path.parent.mkdir(parents=True, exist_ok=True)
        with self._fallback_file_path.open("a", encoding="utf-8") as file_obj:
            for event in events:
                row = {
                    "event_type": event["event_type"],
                    "payload": asdict_safe(event["payload"]),
                }
                file_obj.write(json.dumps(row, ensure_ascii=True) + "\n")


def asdict_safe(payload: Any) -> Any:
    if hasattr(payload, "__dataclass_fields__"):
        return asdict(payload)
    return payload
