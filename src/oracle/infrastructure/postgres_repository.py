import psycopg
import os
from typing import Optional


def get_dsn() -> str:
    return os.getenv("ORACLE_POSTGRES_DSN", "")


def _default_signal_expiry_hours() -> int:
    return int(os.getenv("ORACLE_SIGNAL_EXPIRY_HOURS", "24"))


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
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    expires_at TIMESTAMPTZ,
                    resolved_at TIMESTAMPTZ,
                    resolved_action TEXT,
                    data_timestamp TEXT
                )
            """)

            # Migrations for existing databases
            migration_columns = [
                ("entry_price", "NUMERIC"),
                ("target_price", "NUMERIC"),
                ("stop_loss", "NUMERIC"),
                ("expires_at", "TIMESTAMPTZ"),
                ("resolved_at", "TIMESTAMPTZ"),
                ("resolved_action", "TEXT"),
                ("data_timestamp", "TEXT"),
            ]
            for col_name, col_type in migration_columns:
                try:
                    cur.execute(
                        f"ALTER TABLE signal_history ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                    )
                except Exception:
                    pass

            cur.execute("""
                CREATE TABLE IF NOT EXISTS watchlist (
                    ticker TEXT PRIMARY KEY,
                    added_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS daily_anomalies (
                    ticker TEXT PRIMARY KEY,
                    date_added DATE DEFAULT CURRENT_DATE
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
                    last_checked_at TIMESTAMPTZ DEFAULT NOW(),
                    entry_price NUMERIC,
                    target_price NUMERIC,
                    stop_loss NUMERIC,
                    current_price NUMERIC,
                    pnl_percent NUMERIC DEFAULT 0,
                    signal_id UUID
                )
            """)

            # Migrations for active_tracking
            tracking_columns = [
                ("entry_price", "NUMERIC"),
                ("target_price", "NUMERIC"),
                ("stop_loss", "NUMERIC"),
                ("current_price", "NUMERIC"),
                ("pnl_percent", "NUMERIC DEFAULT 0"),
                ("signal_id", "UUID"),
            ]
            for col_name, col_type in tracking_columns:
                try:
                    cur.execute(
                        f"ALTER TABLE active_tracking ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                    )
                except Exception:
                    pass

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
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_signal_history_expires
                ON signal_history (expires_at)
                WHERE resolved_at IS NULL
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_active_tracking_active
                ON active_tracking (is_active)
                WHERE is_active = TRUE
                """
            )
        conn.commit()


def save_signal(
    ticker: str,
    signal_type: str,
    news: str,
    reasoning: str,
    bias: str,
    entry: float = None,
    tp: float = None,
    sl: float = None,
    data_timestamp: str = None,
) -> Optional[str]:
    """Save a signal and return its UUID. Sets expires_at automatically."""
    dsn = get_dsn()
    if not dsn:
        return None
    expiry_hours = _default_signal_expiry_hours()
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            if bias.upper() == "IGNORE":
                cur.execute(
                    """
                    INSERT INTO signal_history
                        (ticker, technical_signal, news_context, ai_reasoning, bias,
                         entry_price, target_price, stop_loss, data_timestamp,
                         expires_at, resolved_at, resolved_action)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                            NOW() + make_interval(hours => %s), NOW(), 'IGNORE')
                    RETURNING id
                    """,
                    (ticker, signal_type, news, reasoning, bias, entry, tp, sl,
                     data_timestamp, expiry_hours),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO signal_history
                        (ticker, technical_signal, news_context, ai_reasoning, bias,
                         entry_price, target_price, stop_loss, data_timestamp,
                         expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                            NOW() + make_interval(hours => %s))
                    RETURNING id
                    """,
                    (ticker, signal_type, news, reasoning, bias, entry, tp, sl,
                     data_timestamp, expiry_hours),
                )
            row = cur.fetchone()
            signal_id = str(row[0]) if row else None
        conn.commit()
    return signal_id


def resolve_signal_by_ticker(ticker: str, action: str) -> Optional[str]:
    """
    Mark the latest unresolved signal for a ticker as resolved.
    Returns the signal_id if found, None otherwise.
    """
    dsn = get_dsn()
    if not dsn:
        return None
    normalized = ticker.strip().upper()
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE signal_history
                SET resolved_at = NOW(), resolved_action = %s
                WHERE id = (
                    SELECT id FROM signal_history
                    WHERE UPPER(ticker) = %s
                      AND resolved_at IS NULL
                    ORDER BY created_at DESC
                    LIMIT 1
                )
                RETURNING id, entry_price, target_price, stop_loss
                """,
                (action, normalized),
            )
            row = cur.fetchone()
        conn.commit()
    if row:
        return str(row[0])
    return None


def get_signal_prices(signal_ticker: str) -> dict | None:
    """Get entry/target/stop_loss from the latest resolved BUY signal for a ticker."""
    dsn = get_dsn()
    if not dsn:
        return None
    normalized = signal_ticker.strip().upper()
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT entry_price, target_price, stop_loss
                FROM signal_history
                WHERE UPPER(ticker) = %s
                  AND resolved_action = 'BUY'
                ORDER BY resolved_at DESC
                LIMIT 1
                """,
                (normalized,),
            )
            row = cur.fetchone()
    if row:
        return {
            "entry_price": float(row[0]) if row[0] is not None else None,
            "target_price": float(row[1]) if row[1] is not None else None,
            "stop_loss": float(row[2]) if row[2] is not None else None,
        }
    return None


def expire_stale_signals() -> int:
    """Auto-expire signals past their expires_at. Returns count of expired signals."""
    dsn = get_dsn()
    if not dsn:
        return 0
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE signal_history
                SET resolved_at = NOW(), resolved_action = 'EXPIRED'
                WHERE resolved_at IS NULL
                  AND expires_at IS NOT NULL
                  AND expires_at <= NOW()
                """
            )
            count = cur.rowcount
        conn.commit()
    return count


def is_signal_expired_for_ticker(ticker: str) -> bool:
    """Check if the latest signal for a ticker is expired or resolved."""
    dsn = get_dsn()
    if not dsn:
        return True
    normalized = ticker.strip().upper()
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT resolved_at, expires_at
                FROM signal_history
                WHERE UPPER(ticker) = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (normalized,),
            )
            row = cur.fetchone()
    if not row:
        return True
    resolved_at, expires_at = row
    if resolved_at is not None:
        return True
    if expires_at is not None:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) >= expires_at
    return False


def has_pending_signal_for_any(tickers: list[str]) -> bool:
    """
    Check if there is an unresolved, non-expired signal for any of the given tickers.
    This prevents generating duplicate signals while one is still active.
    """
    dsn = get_dsn()
    if not dsn:
        return False
    normalized_tickers = [t.strip().upper() for t in tickers if t and t.strip()]
    if not normalized_tickers:
        return False
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM signal_history
                WHERE UPPER(ticker) = ANY(%s)
                  AND resolved_at IS NULL
                  AND (expires_at IS NULL OR expires_at > NOW())
                LIMIT 1
                """,
                (normalized_tickers,),
            )
            return cur.fetchone() is not None


def is_ticker_actively_tracked(ticker: str) -> bool:
    """Check if a ticker is currently in the active tracking portfolio."""
    dsn = get_dsn()
    if not dsn:
        return False
    normalized = ticker.strip().upper()
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM active_tracking WHERE UPPER(ticker) = %s AND is_active = TRUE",
                (normalized,),
            )
            return cur.fetchone() is not None


def is_ticker_on_ignore(ticker: str) -> bool:
    """Check if a ticker is on the ignore/cooldown list."""
    dsn = get_dsn()
    if not dsn:
        return False
    normalized = ticker.strip().upper()
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM ignore_list WHERE UPPER(ticker) = %s AND expires_at > NOW()",
                (normalized,),
            )
            return cur.fetchone() is not None


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


def save_daily_anomalies(tickers: list[str]) -> None:
    dsn = get_dsn()
    if not dsn:
        return
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            # Delete anomalies that are not from today
            cur.execute("DELETE FROM daily_anomalies WHERE date_added < CURRENT_DATE")
            for ticker in tickers:
                cur.execute(
                    "INSERT INTO daily_anomalies (ticker, date_added) VALUES (%s, CURRENT_DATE) ON CONFLICT (ticker) DO UPDATE SET date_added = CURRENT_DATE",
                    (ticker,)
                )
        conn.commit()


def get_daily_anomalies() -> list[str]:
    dsn = get_dsn()
    if not dsn:
        return []
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT ticker FROM daily_anomalies WHERE date_added = CURRENT_DATE")
            return [r[0] for r in cur.fetchall()]


def track_symbol(
    ticker: str,
    entry_price: float = None,
    target_price: float = None,
    stop_loss: float = None,
    signal_id: str = None,
) -> None:
    dsn = get_dsn()
    if not dsn:
        return
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO active_tracking
                    (ticker, entry_price, target_price, stop_loss, signal_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (ticker, entry_price, target_price, stop_loss, signal_id),
            )
        conn.commit()


def ignore_symbol(ticker: str) -> None:
    dsn = get_dsn()
    if not dsn:
        return
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ignore_list (ticker, expires_at)
                VALUES (%s, NOW() + INTERVAL '3 days')
                """,
                (ticker,),
            )
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


def get_dashboard_signals(
    limit: int = 50,
    unresolved_expiry_hours: int = 24,
) -> list[dict]:
    """
    Fetch signals for the dashboard. Only shows:
    - Unresolved, non-expired signals (pending action)
    - Recently resolved signals (for context)
    Expired signals are auto-hidden.
    """
    dsn = get_dsn()
    if not dsn:
        return []

    # Auto-expire stale signals first
    expire_stale_signals()

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
                        WHEN sh.resolved_action = 'EXPIRED' THEN 'EXPIRED'
                        WHEN sh.resolved_action = 'BUY' THEN 'TRACKING'
                        WHEN sh.resolved_action = 'IGNORE' THEN 'IGNORED'
                        WHEN at.ticker IS NOT NULL THEN 'TRACKING'
                        WHEN it.ticker IS NOT NULL THEN 'IGNORED'
                        ELSE 'PENDING'
                    END AS status,
                    sh.resolved_at,
                    sh.expires_at,
                    sh.data_timestamp
                FROM signal_history sh
                LEFT JOIN active_tickers at ON UPPER(at.ticker) = UPPER(sh.ticker)
                LEFT JOIN ignored_tickers it ON UPPER(it.ticker) = UPPER(sh.ticker)
                WHERE (
                    sh.resolved_at IS NULL
                    OR sh.created_at >= NOW() - make_interval(hours => %s)
                )
                ORDER BY
                    CASE WHEN sh.resolved_at IS NULL THEN 0 ELSE 1 END,
                    sh.created_at DESC
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
                    "resolved_at": row[11].isoformat() if row[11] else None,
                    "expires_at": row[12].isoformat() if row[12] else None,
                    "data_timestamp": row[13],
                })
            return signals


def get_portfolio() -> list[dict]:
    """Fetch active portfolio positions (all tracked symbols)."""
    dsn = get_dsn()
    if not dsn:
        return []
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id, ticker, tracked_since, last_checked_at,
                    entry_price, target_price, stop_loss,
                    current_price, pnl_percent
                FROM active_tracking
                WHERE is_active = TRUE
                ORDER BY tracked_since DESC
                """
            )
            rows = cur.fetchall()
            positions = []
            for r in rows:
                positions.append({
                    "id": str(r[0]),
                    "ticker": r[1],
                    "tracked_since": r[2].isoformat() if r[2] else None,
                    "last_checked_at": r[3].isoformat() if r[3] else None,
                    "entry_price": float(r[4]) if r[4] is not None else None,
                    "target_price": float(r[5]) if r[5] is not None else None,
                    "stop_loss": float(r[6]) if r[6] is not None else None,
                    "current_price": float(r[7]) if r[7] is not None else None,
                    "pnl_percent": float(r[8]) if r[8] is not None else None,
                })
            return positions


def get_signal_history(limit: int = 50) -> list[dict]:
    """Fetch resolved/expired signal history."""
    dsn = get_dsn()
    if not dsn:
        return []
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id, ticker, bias, ai_reasoning, entry_price, target_price, stop_loss,
                    created_at, resolved_at, resolved_action
                FROM signal_history
                WHERE resolved_at IS NOT NULL
                ORDER BY resolved_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
            history = []
            for r in rows:
                history.append({
                    "id": str(r[0]),
                    "ticker": r[1],
                    "bias": r[2],
                    "ai_reasoning": r[3],
                    "entry_price": float(r[4]) if r[4] is not None else None,
                    "target_price": float(r[5]) if r[5] is not None else None,
                    "stop_loss": float(r[6]) if r[6] is not None else None,
                    "created_at": r[7].isoformat() if r[7] else None,
                    "resolved_at": r[8].isoformat() if r[8] else None,
                    "resolved_action": r[9],
                })
            return history


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
                SELECT id, ticker, tracked_since, last_checked_at,
                       entry_price, target_price, stop_loss, current_price
                FROM active_tracking
                WHERE is_active = TRUE
            """)
            rows = cur.fetchall()
            return [
                {
                    "id": str(r[0]),
                    "ticker": r[1],
                    "tracked_since": r[2],
                    "last_checked_at": r[3],
                    "entry_price": float(r[4]) if r[4] is not None else None,
                    "target_price": float(r[5]) if r[5] is not None else None,
                    "stop_loss": float(r[6]) if r[6] is not None else None,
                    "current_price": float(r[7]) if r[7] is not None else None,
                }
                for r in rows
            ]


def update_tracking_price(tracking_id: str, current_price: float, pnl_percent: float) -> None:
    """Update the live price and PnL for a tracked position."""
    dsn = get_dsn()
    if not dsn:
        return
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE active_tracking
                SET current_price = %s, pnl_percent = %s, last_checked_at = NOW()
                WHERE id = %s
                """,
                (current_price, pnl_percent, tracking_id),
            )
        conn.commit()


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


def save_tracking_alert(tracking_id: str, alert_type: str, message: str) -> None:
    """Log an alert that was sent for a tracked position."""
    dsn = get_dsn()
    if not dsn:
        return
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tracking_alerts (tracking_id, alert_type, message)
                VALUES (%s, %s, %s)
                """,
                (tracking_id, alert_type, message),
            )
        conn.commit()
