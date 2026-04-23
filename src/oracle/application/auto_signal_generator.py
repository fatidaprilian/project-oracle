import os
import asyncio
import httpx
import json
import logging
from datetime import date, datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from oracle.application.signal_synthesizer import fetch_news_for_ticker
from oracle.infrastructure.postgres_repository import (
    get_watchlist,
    has_signal_today_for_any,
    save_signal,
)
from google import genai
from pydantic import BaseModel, Field


DEFAULT_WATCHLIST = ["AAPL", "NVDA", "TSLA", "BBCA.JK", "GOTO.JK", "AMZN"]
_AUTO_SIGNAL_SCHEDULER: AsyncIOScheduler | None = None
_LAST_ACTIONABLE_SIGNAL_AT: datetime | None = None
_LAST_HEARTBEAT_SENT_AT: datetime | None = None
_INVALID_TICKER_UNTIL: dict[str, datetime] = {}
_LAST_ANALYSIS_DAY_BY_TICKER: dict[str, date] = {}

class AutoSignalDecision(BaseModel):
    bias: str = Field(description="Must be BUY, SELL, or IGNORE")
    reason: str = Field(description="Max 2 sentences of reasoning")
    entry_price: float = Field(description="Suggested entry price", default=0.0)
    target_price: float = Field(description="Suggested take profit price", default=0.0)
    stop_loss: float = Field(description="Suggested stop loss price", default=0.0)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_bias(raw_bias: object) -> str:
    return str(raw_bias or "IGNORE").strip().upper()


def _safe_float(raw_value: object) -> float | None:
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return None


def _normalize_ticker(raw_ticker: str) -> str:
    return raw_ticker.strip().upper()


def _get_alt_suffixes() -> list[str]:
    raw_suffixes = os.getenv("ORACLE_AUTO_SIGNAL_ALT_SUFFIXES", ".JK")
    suffixes = [segment.strip().upper() for segment in raw_suffixes.split(",")]
    return [suffix for suffix in suffixes if suffix]


def _build_ticker_candidates(ticker: str) -> list[str]:
    normalized = _normalize_ticker(ticker)
    candidates = [normalized]
    if "." not in normalized:
        for suffix in _get_alt_suffixes():
            alias = f"{normalized}{suffix}"
            if alias not in candidates:
                candidates.append(alias)
    return candidates


def _is_on_invalid_cooldown(ticker: str, now: datetime) -> bool:
    expiry = _INVALID_TICKER_UNTIL.get(ticker)
    if expiry is None:
        return False
    if now >= expiry:
        _INVALID_TICKER_UNTIL.pop(ticker, None)
        return False
    return True


def _mark_invalid_cooldown(ticker: str, now: datetime) -> None:
    cooldown_hours = float(
        os.getenv("ORACLE_AUTO_SIGNAL_INVALID_TICKER_COOLDOWN_HOURS", "24")
    )
    _INVALID_TICKER_UNTIL[ticker] = now + timedelta(hours=max(cooldown_hours, 1.0))


def _is_already_analyzed_today(tickers: list[str], current_day: date) -> bool:
    for ticker in tickers:
        normalized_ticker = _normalize_ticker(ticker)
        if _LAST_ANALYSIS_DAY_BY_TICKER.get(normalized_ticker) == current_day:
            return True
    return False


def _mark_analyzed_today(tickers: list[str], current_day: date) -> None:
    for ticker in tickers:
        normalized_ticker = _normalize_ticker(ticker)
        if normalized_ticker:
            _LAST_ANALYSIS_DAY_BY_TICKER[normalized_ticker] = current_day


def _load_technical_data(yf_module: object, ticker: str) -> tuple[str | None, str | None]:
    errors: list[str] = []
    for candidate in _build_ticker_candidates(ticker):
        try:
            stock = yf_module.Ticker(candidate)
            hist = stock.history(period="1mo")
            if hist.empty:
                errors.append(f"No price data for {candidate}")
                continue

            current_price = hist["Close"].iloc[-1]
            high_30d = hist["High"].max()
            low_30d = hist["Low"].min()
            volume = hist["Volume"].iloc[-1]

            technical_context = f"Current Price: {current_price:.2f}\n"
            technical_context += f"30-Day High (Resistance): {high_30d:.2f}\n"
            technical_context += f"30-Day Low (Support): {low_30d:.2f}\n"
            technical_context += f"Latest Volume: {volume}"
            return candidate, technical_context
        except Exception as e:
            errors.append(f"{candidate}: {e}")

    return None, "; ".join(errors) if errors else "No price data"


def _should_send_stale_heartbeat(now: datetime, stale_hours: float, cooldown_minutes: int) -> bool:
    if _LAST_ACTIONABLE_SIGNAL_AT is None:
        return False

    stale_threshold = timedelta(hours=max(stale_hours, 0.5))
    elapsed_since_actionable = now - _LAST_ACTIONABLE_SIGNAL_AT
    if elapsed_since_actionable < stale_threshold:
        return False

    if _LAST_HEARTBEAT_SENT_AT is None:
        return True

    heartbeat_cooldown = timedelta(minutes=max(cooldown_minutes, 1))
    return (now - _LAST_HEARTBEAT_SENT_AT) >= heartbeat_cooldown


async def _send_telegram_message(
    bot_token: str,
    chat_id: str,
    text: str,
    reply_markup: dict | None = None,
) -> bool:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    try:
        async with httpx.AsyncClient(timeout=20.0) as http_client:
            response = await http_client.post(url, json=payload)
            response.raise_for_status()
        return True
    except Exception as e:
        print(f"Failed to send telegram message: {e}")
        return False

async def generate_auto_signals():
    global _LAST_ACTIONABLE_SIGNAL_AT
    global _LAST_HEARTBEAT_SENT_AT

    print("Running Auto Signal Generator Daemon (Pro 2026)...")
    
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    api_key = os.getenv("ORACLE_AI_ANALYST_API_KEY")
    
    if not telegram_bot_token or not telegram_chat_id or not api_key:
        print("Missing credentials for Auto Signal Generator")
        return

    postgres_enabled = os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() == "true"

    if _LAST_ACTIONABLE_SIGNAL_AT is None:
        _LAST_ACTIONABLE_SIGNAL_AT = _utc_now()

    try:
        import yfinance as yf
    except Exception as e:
        print(f"Missing dependency yfinance for Auto Signal Generator: {e}")
        return

    # Reduce noisy yfinance stderr logs on invalid symbols; we handle retries/fallbacks ourselves.
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)
        
    client = genai.Client(api_key=api_key)

    # 1. Fetch Dynamic Watchlist
    try:
        watchlist = get_watchlist()
    except Exception as e:
        print(f"Failed to fetch watchlist from DB: {e}")
        watchlist = DEFAULT_WATCHLIST
        
    if not watchlist:
        watchlist = DEFAULT_WATCHLIST

    actionable_signals = 0

    for raw_ticker in watchlist:
        ticker = _normalize_ticker(raw_ticker)
        now = _utc_now()
        ticker_candidates = _build_ticker_candidates(ticker)
        current_day = now.date()

        if postgres_enabled:
            try:
                if has_signal_today_for_any(ticker_candidates):
                    print(f"Skipping {ticker}: already analyzed today")
                    _mark_analyzed_today(ticker_candidates, current_day)
                    continue
            except Exception as e:
                print(f"Failed daily analysis check for {ticker}: {e}")

        if _is_already_analyzed_today(ticker_candidates, current_day):
            print(f"Skipping {ticker}: already analyzed today (in-memory)")
            continue

        if _is_on_invalid_cooldown(ticker, now):
            print(f"Skipping {ticker}: on invalid-symbol cooldown")
            continue

        print(f"Analyzing {ticker} for auto-signal...")
        
        # 2. Fetch Fundamental News
        news = fetch_news_for_ticker(ticker, max_headlines=5)
        
        # 3. Fetch Technical Data via yfinance with ticker fallback aliases.
        resolved_ticker, technical_context = _load_technical_data(yf, ticker)
        if resolved_ticker is None:
            print(f"No price data for {ticker}. Details: {technical_context}")
            _mark_invalid_cooldown(ticker, now)
            continue

        if resolved_ticker != ticker:
            print(f"Using fallback symbol {resolved_ticker} for {ticker}")

        # 4. Synthesize with Gemini
        prompt = f"""
You are Oracle Pro 2026, an elite quantitative analyst.
Analyze the following stock: {resolved_ticker}

TECHNICAL DATA:
{technical_context}

FUNDAMENTAL NEWS:
{news}

Determine if this is a BUY, SELL, or IGNORE.
If BUY or SELL, you MUST provide explicit entry_price, target_price (Take Profit), and stop_loss based on the 30-day support/resistance levels.
Keep reasoning under 2 sentences.
"""
        try:
            response = client.models.generate_content(
                model='gemini-2.5-pro',
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': AutoSignalDecision,
                    'temperature': 0.2,
                },
            )
            decision = json.loads(response.text)
            bias = _normalize_bias(decision.get("bias"))
            entry_price = _safe_float(decision.get("entry_price"))
            target_price = _safe_float(decision.get("target_price"))
            stop_loss = _safe_float(decision.get("stop_loss"))
            reason = str(decision.get("reason", "No reasoning provided."))

            if postgres_enabled:
                try:
                    save_signal(
                        ticker=resolved_ticker,
                        signal_type="AI_PRO_SCAN",
                        news=news,
                        reasoning=reason,
                        bias=bias,
                        entry=entry_price,
                        tp=target_price,
                        sl=stop_loss,
                    )
                except Exception as e:
                    print(f"Failed to save auto signal to DB: {e}")

            _mark_analyzed_today(
                [resolved_ticker, *ticker_candidates],
                current_day,
            )
            
            # 5. Push if strong bias
            if bias in ["BUY", "SELL"]:
                actionable_signals += 1
                _LAST_ACTIONABLE_SIGNAL_AT = _utc_now()

                # Send to Telegram
                bias_emoji = "✅" if bias == "BUY" else "🔴"
                message = f"🤖 *Oracle Pro Signal*\n"
                message += f"Ticker: `{resolved_ticker}`\n\n"
                message += f"*Bias:* {bias_emoji} {bias}\n"
                message += f"*Entry:* {entry_price if entry_price is not None else 'N/A'}\n"
                message += f"*Target:* {target_price if target_price is not None else 'N/A'}\n"
                message += f"*Stop Loss:* {stop_loss if stop_loss is not None else 'N/A'}\n\n"
                message += f"*Reasoning:* {reason}"

                await _send_telegram_message(
                    telegram_bot_token,
                    telegram_chat_id,
                    message,
                    reply_markup={
                        "inline_keyboard": [
                            [
                                {"text": "✅ Beli/Track", "callback_data": f"buy_{resolved_ticker}"},
                                {"text": "❌ Abaikan", "callback_data": f"ignore_{resolved_ticker}"},
                            ]
                        ]
                    },
                )
        except Exception as e:
            print(f"Failed Gemini analysis for {ticker}: {e}")
            
        await asyncio.sleep(4)

    heartbeat_enabled = os.getenv(
        "ORACLE_AUTO_SIGNAL_HEARTBEAT_ENABLED", "true"
    ).lower() == "true"
    stale_hours = float(os.getenv("ORACLE_AUTO_SIGNAL_STALE_HOURS", "3"))
    heartbeat_cooldown_minutes = int(
        os.getenv("ORACLE_AUTO_SIGNAL_HEARTBEAT_COOLDOWN_MINUTES", "180")
    )

    now = _utc_now()
    if heartbeat_enabled and actionable_signals == 0 and _should_send_stale_heartbeat(
        now,
        stale_hours,
        heartbeat_cooldown_minutes,
    ):
        last_actionable_hours = round(
            (now - _LAST_ACTIONABLE_SIGNAL_AT).total_seconds() / 3600,
            1,
        )
        heartbeat_message = (
            "🤖 *Oracle Auto Signal Heartbeat*\n"
            f"Tidak ada BUY/SELL selama ~{last_actionable_hours} jam.\n"
            f"Watchlist dipindai: {len(watchlist)} ticker.\n"
            "Sistem tetap aktif dan akan kirim sinyal saat setup valid muncul."
        )
        sent = await _send_telegram_message(
            telegram_bot_token,
            telegram_chat_id,
            heartbeat_message,
        )
        if sent:
            _LAST_HEARTBEAT_SENT_AT = now

def start_auto_signal_daemon():
    global _AUTO_SIGNAL_SCHEDULER

    if _AUTO_SIGNAL_SCHEDULER is not None and _AUTO_SIGNAL_SCHEDULER.running:
        print("Auto Signal Daemon already running, skipping re-initialization.")
        return

    interval_hours = max(int(os.getenv("ORACLE_AUTO_SIGNAL_HOURS", "2")), 1)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        generate_auto_signals,
        "interval",
        hours=interval_hours,
        id="auto_signal_scan",
        next_run_time=_utc_now(),
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )
    scheduler.start()
    _AUTO_SIGNAL_SCHEDULER = scheduler
    print(
        "Auto Signal Daemon (Pro) started. "
        f"Scanning every {interval_hours} hours (first scan runs immediately)."
    )
