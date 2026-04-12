from __future__ import annotations

from oracle.application.paper_pipeline import run_paper_cycle
from oracle.runtime import build_runtime_components
from oracle.domain.models import MarketSnapshot


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
    snapshot = build_demo_snapshot()
    runtime = build_runtime_components()

    run_paper_cycle(
        snapshot,
        runtime.sentiment_provider,
        runtime.journal,
        runtime.risk_guard,
    )

    runtime.journal.flush()
    if runtime.risk_state_store is not None:
        runtime.risk_state_store.save_state(runtime.risk_guard.state)

    for event in runtime.journal.dump():
        print(event)


if __name__ == "__main__":
    main()
