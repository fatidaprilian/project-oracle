from __future__ import annotations

from dataclasses import dataclass
import os

from oracle.application.risk_controls import RiskConfig, RiskGuard, RiskState
from oracle.infrastructure.external_sentiment_provider import (
    ExternalSentimentConfig,
    ExternalSentimentProvider,
)
from oracle.infrastructure.journal import InMemoryJournal, JournalSink
from oracle.infrastructure.postgres_journal_repository import PostgresJournalRepository
from oracle.infrastructure.redis_risk_repository import RedisRiskRepository
from oracle.modules.sentiment_gate import SentimentProvider, StaticSentimentProvider


@dataclass(frozen=True)
class RuntimeSettings:
    postgres_dsn: str
    redis_url: str
    enable_postgres_persistence: bool
    enable_redis_risk_state: bool


@dataclass
class RuntimeComponents:
    journal: InMemoryJournal
    risk_guard: RiskGuard
    sentiment_provider: SentimentProvider
    risk_state_store: RedisRiskRepository | None


def build_runtime_settings() -> RuntimeSettings:
    postgres_dsn = os.getenv("ORACLE_POSTGRES_DSN", "")
    redis_url = os.getenv("ORACLE_REDIS_URL", "")
    enable_postgres_persistence = os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() == "true"
    enable_redis_risk_state = os.getenv("ORACLE_ENABLE_REDIS", "false").lower() == "true"

    return RuntimeSettings(
        postgres_dsn=postgres_dsn,
        redis_url=redis_url,
        enable_postgres_persistence=enable_postgres_persistence,
        enable_redis_risk_state=enable_redis_risk_state,
    )


def build_runtime_components() -> RuntimeComponents:
    settings = build_runtime_settings()

    journal_sink: JournalSink | None = None
    if settings.enable_postgres_persistence and settings.postgres_dsn:
        journal_sink = PostgresJournalRepository(settings.postgres_dsn)

    journal = InMemoryJournal(journal_sink)

    risk_state_store: RedisRiskRepository | None = None
    risk_state = RiskState()
    if settings.enable_redis_risk_state and settings.redis_url:
        risk_state_store = RedisRiskRepository(settings.redis_url)
        risk_state = risk_state_store.load_state()

    risk_guard = RiskGuard(RiskConfig(), risk_state)

    sentiment_base_url = os.getenv("ORACLE_SENTIMENT_BASE_URL", "")
    sentiment_api_key = os.getenv("ORACLE_SENTIMENT_API_KEY", "")
    if sentiment_base_url and sentiment_api_key:
        sentiment_provider = ExternalSentimentProvider(
            ExternalSentimentConfig.from_env()
        )
    else:
        sentiment_provider = StaticSentimentProvider()

    return RuntimeComponents(
        journal=journal,
        risk_guard=risk_guard,
        sentiment_provider=sentiment_provider,
        risk_state_store=risk_state_store,
    )