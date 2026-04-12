from __future__ import annotations

from oracle.application.paper_pipeline import run_paper_cycle
from oracle.domain.models import MarketSnapshot
from oracle.infrastructure.journal import InMemoryJournal
from oracle.modules.sentiment_gate import StaticSentimentProvider


def build_demo_snapshot() -> MarketSnapshot:
    return MarketSnapshot(
        symbol="BTCUSDT",
        timeframe="15m",
        closes=[100.0, 101.2, 102.4, 103.1, 103.8],
        highs=[100.7, 101.8, 102.9, 103.5, 104.1],
        lows=[99.6, 100.8, 101.9, 102.5, 103.0],
        current_price=103.4,
        volume=1200.0,
    )


def main() -> None:
    journal = InMemoryJournal()
    snapshot = build_demo_snapshot()
    sentiment_provider = StaticSentimentProvider()

    run_paper_cycle(snapshot, sentiment_provider, journal)

    for event in journal.dump():
        print(event)


if __name__ == "__main__":
    main()
