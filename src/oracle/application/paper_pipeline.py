from __future__ import annotations

from oracle.domain.models import MarketSnapshot, PositionState
from oracle.infrastructure.journal import InMemoryJournal
from oracle.modules.confluence_engine import evaluate_confluence
from oracle.modules.exit_engine import evaluate_exit
from oracle.modules.sentiment_gate import SentimentProvider, evaluate_sentiment
from oracle.modules.sniper_entry import build_entry_plan
from oracle.modules.structure_engine import evaluate_structure
from oracle.modules.zone_engine import detect_zone


def run_paper_cycle(
    snapshot: MarketSnapshot,
    sentiment_provider: SentimentProvider,
    journal: InMemoryJournal,
) -> None:
    structure = evaluate_structure(snapshot)
    journal.record("structure_evaluated", structure)

    if not structure.is_tradeable:
        journal.record("candidate_rejected", {"reason": "REGIME_NOT_TRADEABLE"})
        return

    zone = detect_zone(snapshot, structure)
    journal.record("zone_detected", zone)

    confluence = evaluate_confluence(snapshot, zone)
    journal.record("confluence_evaluated", confluence)

    sentiment = evaluate_sentiment(snapshot.symbol, sentiment_provider)
    journal.record("sentiment_evaluated", sentiment)

    entry_plan = build_entry_plan(snapshot, zone, confluence, sentiment)
    journal.record("entry_planned", entry_plan)

    if not entry_plan.should_place_order:
        journal.record("candidate_rejected", {"reason": entry_plan.reason_codes})
        return

    position = PositionState(
        symbol=snapshot.symbol,
        side="long",
        entry_price=entry_plan.entry_price,
        stop_loss=entry_plan.stop_loss,
        take_profit_primary=entry_plan.take_profit_primary,
        take_profit_secondary=entry_plan.take_profit_secondary,
    )
    journal.record("position_opened", position)

    exit_decision = evaluate_exit(position, snapshot.current_price)
    journal.record("exit_evaluated", exit_decision)

    if exit_decision.exit_reason == "BREAK_EVEN_ARMED":
        position.stop_loss = exit_decision.updated_stop_loss
        position.is_break_even_armed = True
        journal.record("position_updated", position)

    if exit_decision.should_close:
        position.is_open = False
        journal.record("position_closed", {"reason": exit_decision.exit_reason})
