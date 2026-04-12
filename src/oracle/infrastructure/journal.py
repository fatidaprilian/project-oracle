from __future__ import annotations

from dataclasses import asdict
from typing import Any


class InMemoryJournal:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record(self, event_type: str, payload: Any) -> None:
        if hasattr(payload, "__dataclass_fields__"):
            serialized = asdict(payload)
        else:
            serialized = payload
        self.events.append({"event_type": event_type, "payload": serialized})

    def dump(self) -> list[dict[str, Any]]:
        return self.events.copy()
