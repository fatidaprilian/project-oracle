from __future__ import annotations

from oracle.domain.models import ExitDecision, PositionState


def evaluate_exit(position: PositionState, current_price: float) -> ExitDecision:
    risk = max(position.entry_price - position.stop_loss, position.entry_price * 0.001)
    reward = current_price - position.entry_price

    if reward >= risk and not position.is_break_even_armed:
        return ExitDecision(
            should_close=False,
            exit_reason="BREAK_EVEN_ARMED",
            updated_stop_loss=position.entry_price,
        )

    if current_price >= position.take_profit_primary:
        return ExitDecision(
            should_close=True,
            exit_reason="FIB_EXTENSION_TP_HIT",
            updated_stop_loss=position.stop_loss,
        )

    if current_price <= position.stop_loss:
        return ExitDecision(
            should_close=True,
            exit_reason="STRUCTURAL_SHIFT_EXIT",
            updated_stop_loss=position.stop_loss,
        )

    return ExitDecision(
        should_close=False,
        exit_reason="HOLD",
        updated_stop_loss=position.stop_loss,
    )
