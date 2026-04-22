import psycopg
import os
from typing import Optional

def get_dsn() -> str:
    return os.getenv("ORACLE_POSTGRES_DSN", "")

def init_db() -> None:
    dsn = get_dsn()
    if not dsn:
        return
        
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS signal_history (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    ticker TEXT NOT NULL,
                    technical_signal TEXT NOT NULL,
                    news_context TEXT,
                    ai_reasoning TEXT,
                    bias TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS active_tracking (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    ticker TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    tracked_since TIMESTAMPTZ DEFAULT NOW(),
                    last_checked_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ignore_list (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    ticker TEXT NOT NULL,
                    expires_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tracking_alerts (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tracking_id UUID REFERENCES active_tracking(id),
                    alert_type TEXT,
                    message TEXT,
                    sent_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
        conn.commit()

def save_signal(ticker: str, signal_type: str, news: str, reasoning: str, bias: str) -> None:
    dsn = get_dsn()
    if not dsn:
        return
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO signal_history (ticker, technical_signal, news_context, ai_reasoning, bias)
                VALUES (%s, %s, %s, %s, %s)
            """, (ticker, signal_type, news, reasoning, bias))
        conn.commit()

def track_symbol(ticker: str) -> None:
    dsn = get_dsn()
    if not dsn:
        return
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO active_tracking (ticker) VALUES (%s)
            """, (ticker,))
        conn.commit()

def ignore_symbol(ticker: str) -> None:
    dsn = get_dsn()
    if not dsn:
        return
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ignore_list (ticker, expires_at) 
                VALUES (%s, NOW() + INTERVAL '3 days')
            """, (ticker,))
        conn.commit()
