from __future__ import annotations

from dataclasses import asdict
from typing import Any, Protocol


class JournalSink(Protocol):
    def save_events(self, events: list[dict[str, Any]]) -> None:
        ...


class InMemoryJournal:
    def __init__(self, sink: JournalSink | None = None) -> None:
        self.events: list[dict[str, Any]] = []
        self._sink = sink

    def record(self, event_type: str, payload: Any) -> None:
        if hasattr(payload, "__dataclass_fields__"):
            serialized = asdict(payload)
        else:
            serialized = payload
        self.events.append({"event_type": event_type, "payload": serialized})

    def dump(self) -> list[dict[str, Any]]:
        return self.events.copy()

    def flush(self) -> None:
        if self._sink is not None:
            self._sink.save_events(self.events)
