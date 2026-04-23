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
                    entry_price NUMERIC,
                    target_price NUMERIC,
                    stop_loss NUMERIC,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            # For migrations on existing DB:
            try:
                cur.execute("ALTER TABLE signal_history ADD COLUMN IF NOT EXISTS entry_price NUMERIC")
                cur.execute("ALTER TABLE signal_history ADD COLUMN IF NOT EXISTS target_price NUMERIC")
                cur.execute("ALTER TABLE signal_history ADD COLUMN IF NOT EXISTS stop_loss NUMERIC")
            except Exception:
                pass
                
            cur.execute("""
                CREATE TABLE IF NOT EXISTS watchlist (
                    ticker TEXT PRIMARY KEY,
                    added_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            # Insert default watchlist if empty
            cur.execute("SELECT COUNT(*) FROM watchlist")
            if cur.fetchone()[0] == 0:
                default_tickers = ["AAPL", "NVDA", "TSLA", "BBCA.JK", "GOTO.JK", "AMZN"]
                for t in default_tickers:
                    cur.execute("INSERT INTO watchlist (ticker) VALUES (%s) ON CONFLICT DO NOTHING", (t,))
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
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_signal_history_ticker_created_at
                ON signal_history (ticker, created_at DESC)
                """
            )
        conn.commit()

def save_signal(ticker: str, signal_type: str, news: str, reasoning: str, bias: str, entry: float = None, tp: float = None, sl: float = None) -> None:
    dsn = get_dsn()
    if not dsn:
        return
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO signal_history (ticker, technical_signal, news_context, ai_reasoning, bias, entry_price, target_price, stop_loss)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (ticker, signal_type, news, reasoning, bias, entry, tp, sl))
        conn.commit()

def get_watchlist() -> list[str]:
    dsn = get_dsn()
    if not dsn:
        return []
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT ticker FROM watchlist ORDER BY added_at DESC")
            return [r[0] for r in cur.fetchall()]

def add_to_watchlist(ticker: str) -> None:
    dsn = get_dsn()
    if not dsn:
        return
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO watchlist (ticker) VALUES (%s) ON CONFLICT DO NOTHING", (ticker,))
        conn.commit()

def remove_from_watchlist(ticker: str) -> None:
    dsn = get_dsn()
    if not dsn:
        return
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM watchlist WHERE ticker = %s", (ticker,))
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

def get_recent_signals(limit: int = 20) -> list[dict]:
    dsn = get_dsn()
    if not dsn:
        return []
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, ticker, technical_signal, news_context, ai_reasoning, bias, created_at, entry_price, target_price, stop_loss
                FROM signal_history
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            
            signals = []
            for row in rows:
                signals.append({
                    "id": str(row[0]),
                    "ticker": row[1],
                    "technical_signal": row[2],
                    "news_context": row[3],
                    "ai_reasoning": row[4],
                    "bias": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                    "entry_price": float(row[7]) if row[7] is not None else None,
                    "target_price": float(row[8]) if row[8] is not None else None,
                    "stop_loss": float(row[9]) if row[9] is not None else None
                })
            return signals


def has_signal_today_for_any(tickers: list[str]) -> bool:
    dsn = get_dsn()
    if not dsn:
        return False

    normalized_tickers = [ticker.strip().upper() for ticker in tickers if ticker and ticker.strip()]
    if not normalized_tickers:
        return False

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM signal_history
                WHERE UPPER(ticker) = ANY(%s)
                  AND created_at >= date_trunc('day', NOW())
                LIMIT 1
                """,
                (normalized_tickers,),
            )
            return cur.fetchone() is not None


def has_signal_today(ticker: str) -> bool:
    return has_signal_today_for_any([ticker])


def get_dashboard_signals(
    limit: int = 50,
    unresolved_expiry_hours: int = 24,
) -> list[dict]:
    dsn = get_dsn()
    if not dsn:
        return []

    expiry_hours = max(int(unresolved_expiry_hours), 1)

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH active_tickers AS (
                    SELECT DISTINCT ticker
                    FROM active_tracking
                    WHERE is_active = TRUE
                ),
                ignored_tickers AS (
                    SELECT DISTINCT ticker
                    FROM ignore_list
                    WHERE expires_at > NOW()
                )
                SELECT
                    sh.id,
                    sh.ticker,
                    sh.technical_signal,
                    sh.news_context,
                    sh.ai_reasoning,
                    sh.bias,
                    sh.created_at,
                    sh.entry_price,
                    sh.target_price,
                    sh.stop_loss,
                    CASE
                        WHEN at.ticker IS NOT NULL THEN 'TRACKING'
                        WHEN it.ticker IS NOT NULL THEN 'IGNORED'
                        ELSE 'NONE'
                    END AS status
                FROM signal_history sh
                LEFT JOIN active_tickers at ON at.ticker = sh.ticker
                LEFT JOIN ignored_tickers it ON it.ticker = sh.ticker
                WHERE (
                    sh.created_at >= NOW() - make_interval(hours => %s)
                    OR at.ticker IS NOT NULL
                    OR it.ticker IS NOT NULL
                )
                ORDER BY sh.created_at DESC
                LIMIT %s
                """,
                (expiry_hours, limit),
            )
            rows = cur.fetchall()

            signals = []
            for row in rows:
                signals.append({
                    "id": str(row[0]),
                    "ticker": row[1],
                    "technical_signal": row[2],
                    "news_context": row[3],
                    "ai_reasoning": row[4],
                    "bias": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                    "entry_price": float(row[7]) if row[7] is not None else None,
                    "target_price": float(row[8]) if row[8] is not None else None,
                    "stop_loss": float(row[9]) if row[9] is not None else None,
                    "status": row[10],
                })
            return signals

def get_tracking_status(ticker: str) -> str:
    dsn = get_dsn()
    if not dsn:
        return "NONE"
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM active_tracking WHERE ticker = %s AND is_active = TRUE", (ticker,))
            if cur.fetchone():
                return "TRACKING"
            cur.execute("SELECT 1 FROM ignore_list WHERE ticker = %s AND expires_at > NOW()", (ticker,))
            if cur.fetchone():
                return "IGNORED"
    return "NONE"

def get_active_trackings() -> list[dict]:
    dsn = get_dsn()
    if not dsn:
        return []
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, ticker, tracked_since, last_checked_at
                FROM active_tracking
                WHERE is_active = TRUE
            """)
            rows = cur.fetchall()
            return [{"id": str(r[0]), "ticker": r[1]} for r in rows]

def update_last_checked(tracking_id: str) -> None:
    dsn = get_dsn()
    if not dsn:
        return
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE active_tracking 
                SET last_checked_at = NOW() 
                WHERE id = %s
            """, (tracking_id,))
        conn.commit()

def close_tracking(ticker: str) -> None:
    dsn = get_dsn()
    if not dsn:
        return
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE active_tracking 
                SET is_active = FALSE 
                WHERE ticker = %s AND is_active = TRUE
            """, (ticker,))
            # Add to ignore list so we don't buy it again immediately
            cur.execute("""
                INSERT INTO ignore_list (ticker, expires_at) 
                VALUES (%s, NOW() + INTERVAL '3 days')
            """, (ticker,))
        conn.commit()
