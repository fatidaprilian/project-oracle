from __future__ import annotations

from typing import Protocol

from oracle.domain.models import SentimentSignal


class SentimentProvider(Protocol):
    def get_sentiment_bias(self, symbol: str) -> str:
        ...

    def get_event_risk_level(self, symbol: str) -> str:
        ...


class StaticSentimentProvider:
    def get_sentiment_bias(self, symbol: str) -> str:
        return "neutral"

    def get_event_risk_level(self, symbol: str) -> str:
        return "low"


def evaluate_sentiment(symbol: str, provider: SentimentProvider) -> SentimentSignal:
    bias = provider.get_sentiment_bias(symbol)
    risk = provider.get_event_risk_level(symbol)
    shield_status = risk in {"high", "critical"}

    return SentimentSignal(
        sentiment_bias=bias,
        event_risk_level=risk,
        shield_status=shield_status,
    )
