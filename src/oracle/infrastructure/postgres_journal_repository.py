from __future__ import annotations

from dataclasses import asdict
from typing import Any


class PostgresJournalRepository:
    def __init__(self, dsn: str, table_name: str = "trade_events") -> None:
        self._dsn = dsn
        self._table_name = table_name

    def save_events(self, events: list[dict[str, Any]]) -> None:
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
                        (event["event_type"], asdict_safe(event["payload"])),
                    )
            connection.commit()


def asdict_safe(payload: Any) -> Any:
    if hasattr(payload, "__dataclass_fields__"):
        return asdict(payload)
    return payload
