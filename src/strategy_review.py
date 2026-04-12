from __future__ import annotations

import os
from pathlib import Path

from oracle.application.replay_runner import run_replay
from oracle.application.strategy_intelligence import (
    append_parameter_change_request,
    build_parameter_change_request,
    build_ai_review_packet,
    write_ai_review_packet,
)
from oracle.modules.sentiment_gate import StaticSentimentProvider


def main() -> None:
    events = run_replay(Path("data/replay/sample_snapshots.jsonl"), StaticSentimentProvider())

    ai_provider = os.getenv("ORACLE_AI_PROVIDER", "grok")
    runtime_mode = os.getenv("ORACLE_RUNTIME_MODE", "paper")
    exchange_env = os.getenv("ORACLE_EXCHANGE_ENV", "testnet")

    packet = build_ai_review_packet(
        events=events,
        ai_provider=ai_provider,
        runtime_mode=runtime_mode,
        exchange_env=exchange_env,
        limit=10,
    )

    packet_path = write_ai_review_packet(Path("reports/ai-review"), packet)
    print(f"ai_review_packet={packet_path}")

    request = build_parameter_change_request(
        generated_from=str(packet_path),
        provider=ai_provider,
        status="pending",
        suggested_changes={
            "min_confluence_score": 62.0,
            "min_volume_threshold": 850.0,
            "max_consecutive_losses": 3.0,
        },
    )
    append_parameter_change_request(Path("registry/parameter_change_requests.jsonl"), request)
    print("parameter_change_request_appended=true")


if __name__ == "__main__":
    main()
