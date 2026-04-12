from __future__ import annotations

import json
from pathlib import Path

from oracle.application.paper_pipeline import run_paper_cycle
from oracle.domain.models import MarketSnapshot
from oracle.infrastructure.journal import InMemoryJournal
from oracle.modules.sentiment_gate import SentimentProvider


def _to_snapshot(record: dict[str, object]) -> MarketSnapshot:
    return MarketSnapshot(
        symbol=str(record["symbol"]),
        timeframe=str(record["timeframe"]),
        closes=[float(value) for value in record["closes"]],
        highs=[float(value) for value in record["highs"]],
        lows=[float(value) for value in record["lows"]],
        current_price=float(record["current_price"]),
        volume=float(record["volume"]),
    )


def run_replay(dataset_path: Path, sentiment_provider: SentimentProvider) -> list[dict[str, object]]:
    journal = InMemoryJournal()
    with dataset_path.open("r", encoding="utf-8") as file_obj:
        for line in file_obj:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            snapshot = _to_snapshot(record)
            run_paper_cycle(snapshot, sentiment_provider, journal)
    return journal.dump()
