import os
import asyncio
import httpx
import json
import logging
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from oracle.application.signal_synthesizer import fetch_news_for_ticker
from oracle.domain.models import MarketSnapshot
from oracle.modules.structure_engine import evaluate_structure
from oracle.modules.zone_engine import detect_zone
from oracle.modules.confluence_engine import evaluate_confluence
from oracle.modules.pullback_strategy import evaluate_stock_pullback
from oracle.modules.sniper_entry import build_entry_plan
from oracle.modules.sentiment_gate import StaticSentimentProvider, evaluate_sentiment
from oracle.infrastructure.postgres_repository import (
    get_watchlist,
    has_pending_signal_for_any,
    is_ticker_actively_tracked,
    is_ticker_on_ignore,
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
    reason: str = Field(description="Max 3 sentences of reasoning incorporating both quantitative and fundamental analysis")
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


def _load_market_data(yf_module: object, ticker: str) -> tuple[str | None, MarketSnapshot | None, str | None, str | None]:
    """
    Load market data from yfinance and build a MarketSnapshot.
    Fetches 1 year of daily data to support quantitative modules (pullback needs 200 bars).

    Returns (resolved_ticker, snapshot, basic_technical_context, data_timestamp_label).
    """
    errors: list[str] = []
    for candidate in _build_ticker_candidates(ticker):
        try:
            stock = yf_module.Ticker(candidate)
            # Fetch 1 year for quantitative modules (pullback needs >= 200 bars)
            hist = stock.history(period="1y")
            if hist.empty:
                errors.append(f"No price data for {candidate}")
                continue

            # Determine data freshness
            last_bar_date = hist.index[-1]
            today = datetime.now(timezone.utc).date()

            if hasattr(last_bar_date, 'date'):
                bar_date = last_bar_date.date()
            else:
                bar_date = last_bar_date

            closes = hist["Close"].tolist()
            highs = hist["High"].tolist()
            lows = hist["Low"].tolist()
            volumes = hist["Volume"].tolist()

            current_price = closes[-1]
            latest_volume = volumes[-1] if volumes else 0.0

            if bar_date == today:
                data_label = f"End of Day (EOD) {bar_date.strftime('%d %b %Y')} @ {current_price:.2f}"
            else:
                data_label = f"Closing {bar_date.strftime('%d %b %Y')} @ {current_price:.2f}"

            snapshot = MarketSnapshot(
                symbol=candidate,
                timeframe="1D",
                closes=closes,
                highs=highs,
                lows=lows,
                current_price=current_price,
                volume=latest_volume,
                volumes=volumes,
            )

            # Build basic technical context string for the AI prompt
            high_30d = max(highs[-30:]) if len(highs) >= 30 else max(highs)
            low_30d = min(lows[-30:]) if len(lows) >= 30 else min(lows)

            basic_context = f"Current Price: {current_price:.2f}\n"
            basic_context += f"30-Day High (Resistance): {high_30d:.2f}\n"
            basic_context += f"30-Day Low (Support): {low_30d:.2f}\n"
            basic_context += f"Latest Volume: {latest_volume}\n"
            basic_context += f"Total Daily Bars Available: {len(closes)}\n"
            basic_context += f"Data As Of: {data_label}"

            return candidate, snapshot, basic_context, data_label
        except Exception as e:
            errors.append(f"{candidate}: {e}")

    return None, None, "; ".join(errors) if errors else "No price data", None


def _run_quantitative_pipeline(snapshot: MarketSnapshot) -> dict:
    """
    Run the full quantitative analysis pipeline on a MarketSnapshot.
    Returns a dict with all analysis results and a human-readable summary.
    """
    # 1. Market Structure
    structure = evaluate_structure(snapshot)

    # 2. Supply/Demand Zone
    zone = detect_zone(snapshot, structure)

    # 3. Fibonacci Confluence
    confluence = evaluate_confluence(snapshot, zone)

    # 4. Pullback Strategy (needs 200+ bars)
    pullback = evaluate_stock_pullback(snapshot)

    # 5. Sentiment (static provider since news sentiment is handled by AI)
    sentiment = evaluate_sentiment(snapshot.symbol, StaticSentimentProvider())

    # 6. Entry Plan (Sniper Entry)
    entry_plan = build_entry_plan(snapshot, zone, confluence, sentiment, pullback)

    # Build human-readable summary for the AI prompt
    summary_lines = []
    summary_lines.append(f"Market Regime: {structure.market_regime.value.upper()} (strength: {structure.structure_strength:.0%})")
    summary_lines.append(f"Tradeable: {'YES' if structure.is_tradeable else 'NO'}")
    summary_lines.append(f"Zone: {zone.zone_type.value.upper()} [{zone.zone_low:.2f} - {zone.zone_high:.2f}]")
    summary_lines.append(f"Confluence Score: {confluence.confluence_score:.1f}/100 (Fib 0.618: {confluence.fib_618_price:.2f})")
    summary_lines.append(f"Confluence Valid: {'YES' if confluence.is_valid else 'NO'}")

    if pullback.strategy_name != "NONE":
        summary_lines.append(f"Pullback Strategy: {pullback.strategy_name} (confidence: {pullback.confidence_score:.0f}%)")
    else:
        summary_lines.append(f"Pullback: NO SETUP ({', '.join(pullback.reason_codes)})")

    if pullback.ema_200 > 0:
        summary_lines.append(f"EMA 200: {pullback.ema_200:.2f}")
    if pullback.ma_99 > 0:
        summary_lines.append(f"MA 99: {pullback.ma_99:.2f}")
    if pullback.volume_ratio > 0:
        summary_lines.append(f"Volume Ratio (vs MA20): {pullback.volume_ratio:.2f}x")

    if entry_plan.should_place_order:
        summary_lines.append(f"Quantitative Entry Plan: VALID")
        summary_lines.append(f"  Entry: {entry_plan.entry_price:.2f}")
        summary_lines.append(f"  Stop Loss: {entry_plan.stop_loss:.2f}")
        summary_lines.append(f"  TP1: {entry_plan.take_profit_primary:.2f}")
        summary_lines.append(f"  TP2: {entry_plan.take_profit_secondary:.2f}")
        summary_lines.append(f"  Reason: {', '.join(entry_plan.reason_codes)}")
    else:
        summary_lines.append(f"Quantitative Entry Plan: REJECTED ({', '.join(entry_plan.reason_codes)})")

    return {
        "structure": structure,
        "zone": zone,
        "confluence": confluence,
        "pullback": pullback,
        "entry_plan": entry_plan,
        "summary": "\n".join(summary_lines),
    }


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

    print("Running Auto Signal Generator Daemon (Pro 2026 + Quant Modules)...")

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

    screener_anomalies = []
    try:
        from oracle.application.market_screener import run_market_screener
        screener_anomalies = run_market_screener()
    except Exception as e:
        print(f"Failed to run market screener: {e}")

    # 1. Fetch Dynamic Watchlist
    try:
        db_watchlist = get_watchlist()
    except Exception as e:
        print(f"Failed to fetch watchlist from DB: {e}")
        db_watchlist = []

    if not db_watchlist:
        db_watchlist = DEFAULT_WATCHLIST

    # Combine manual DB watchlist with Screener Anomalies
    # Use dict.fromkeys to remove duplicates while preserving order
    raw_watchlist = list(dict.fromkeys(db_watchlist + screener_anomalies))

    now = _utc_now()
    current_hour = now.hour

    watchlist = []
    for t in raw_watchlist:
        is_indo = t.endswith('.JK')
        if current_hour == 9 and not is_indo:
            continue  # At 16:15 WIB (09:15 UTC), only scan Indonesian stocks
        if current_hour == 21 and is_indo:
            continue  # At 04:15 WIB (21:15 UTC), only scan US/Global stocks
        watchlist.append(t)

    actionable_signals = 0

    for raw_ticker in watchlist:
        ticker = _normalize_ticker(raw_ticker)
        now = _utc_now()
        ticker_candidates = _build_ticker_candidates(ticker)
        current_day = now.date()

        # Anti-spam: Skip tickers that are already actively tracked (bought)
        if postgres_enabled:
            try:
                any_tracked = any(
                    is_ticker_actively_tracked(candidate)
                    for candidate in ticker_candidates
                )
                if any_tracked:
                    print(f"Skipping {ticker}: currently in active portfolio")
                    continue
            except Exception as e:
                print(f"Failed active tracking check for {ticker}: {e}")

        # Anti-spam: Skip tickers that are on ignore/cooldown list
        if postgres_enabled:
            try:
                any_ignored = any(
                    is_ticker_on_ignore(candidate)
                    for candidate in ticker_candidates
                )
                if any_ignored:
                    print(f"Skipping {ticker}: on ignore cooldown")
                    continue
            except Exception as e:
                print(f"Failed ignore check for {ticker}: {e}")

        # Anti-spam: Skip if there is already a pending (unresolved) signal
        if postgres_enabled:
            try:
                if has_pending_signal_for_any(ticker_candidates):
                    print(f"Skipping {ticker}: pending signal awaiting user action")
                    continue
            except Exception as e:
                print(f"Failed pending signal check for {ticker}: {e}")

        # In-memory daily dedup fallback
        if _is_already_analyzed_today(ticker_candidates, current_day):
            print(f"Skipping {ticker}: already analyzed today (in-memory)")
            continue

        if _is_on_invalid_cooldown(ticker, now):
            print(f"Skipping {ticker}: on invalid-symbol cooldown")
            continue

        print(f"Analyzing {ticker} for auto-signal...")

        # 2. Fetch Fundamental News
        news = fetch_news_for_ticker(ticker, max_headlines=5)

        # 3. Fetch Market Data and build MarketSnapshot
        resolved_ticker, snapshot, basic_context, data_label = _load_market_data(yf, ticker)
        if resolved_ticker is None or snapshot is None:
            print(f"No price data for {ticker}. Details: {basic_context}")
            _mark_invalid_cooldown(ticker, now)
            continue

        if resolved_ticker != ticker:
            print(f"Using fallback symbol {resolved_ticker} for {ticker}")

        # 4. Run Quantitative Analysis Pipeline
        quant_results = _run_quantitative_pipeline(snapshot)
        quant_summary = quant_results["summary"]
        entry_plan = quant_results["entry_plan"]

        print(f"  Quant summary for {resolved_ticker}:\n    " + quant_summary.replace("\n", "\n    "))

        # 5. Synthesize with Gemini (AI sees both raw data + quantitative analysis)
        prompt = f"""
You are Oracle Pro 2026, an elite quantitative analyst with access to both fundamental and technical analysis modules.
Analyze the following stock: {resolved_ticker}

PRICE DATA:
{basic_context}

QUANTITATIVE ANALYSIS (from Oracle modules):
{quant_summary}

FUNDAMENTAL NEWS:
{news}

INSTRUCTIONS:
1. Consider the quantitative analysis heavily. If the quant entry plan is VALID with a high confluence score, that is a strong BUY signal.
2. However, if fundamental news is severely negative (bankruptcy, fraud, SEC probe), override to IGNORE regardless of quant signals.
3. If quant says REJECTED, carefully evaluate the context. If the stock is in a massive breakout/momentum phase (e.g. limit-up/ARA in Indonesian market) or has extremely bullish news/volume anomalies, you MAY override the quant rejection and issue a BUY.
4. If you override and issue a BUY, you MUST estimate realistic entry_price, stop_loss, and target_price based on the price data provided. Do not set them to 0.
5. If quant says REJECTED and there is no strong bullish catalyst or momentum, output IGNORE.

Determine if this is a BUY, SELL, or IGNORE.
If BUY or SELL, you MUST provide explicit entry_price, target_price (Take Profit), and stop_loss.
Keep reasoning under 3 sentences. Reference the quantitative signals in your reasoning.
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

            # If quant entry plan is valid and AI agrees on BUY, prefer quant price levels
            if bias == "BUY" and entry_plan.should_place_order:
                entry_price = round(entry_plan.entry_price, 2)
                stop_loss = round(entry_plan.stop_loss, 2)
                target_price = round(entry_plan.take_profit_primary, 2)

            # Only send SELL signals if ticker is actively tracked
            if bias == "SELL":
                any_tracked = False
                if postgres_enabled:
                    try:
                        any_tracked = any(
                            is_ticker_actively_tracked(c) for c in [resolved_ticker, *ticker_candidates]
                        )
                    except Exception:
                        pass
                if not any_tracked:
                    print(f"Suppressing SELL for {resolved_ticker}: not in active portfolio")
                    bias = "IGNORE"

            # Build signal_type descriptor
            pullback = quant_results["pullback"]
            structure = quant_results["structure"]
            signal_type_parts = ["AI_PRO_SCAN"]
            if pullback.strategy_name != "NONE":
                signal_type_parts.append(pullback.strategy_name)
            signal_type_parts.append(structure.market_regime.value.upper())
            signal_type = "+".join(signal_type_parts)

            signal_id = None
            if postgres_enabled:
                try:
                    signal_id = save_signal(
                        ticker=resolved_ticker,
                        signal_type=signal_type,
                        news=news,
                        reasoning=reason,
                        bias=bias,
                        entry=entry_price,
                        tp=target_price,
                        sl=stop_loss,
                        data_timestamp=data_label,
                    )
                except Exception as e:
                    print(f"Failed to save auto signal to DB: {e}")

            _mark_analyzed_today(
                [resolved_ticker, *ticker_candidates],
                current_day,
            )

            # 6. Push if strong bias
            if bias in ["BUY", "SELL"]:
                actionable_signals += 1
                _LAST_ACTIONABLE_SIGNAL_AT = _utc_now()

                expiry_hours = int(os.getenv("ORACLE_SIGNAL_EXPIRY_HOURS", "24"))

                buy_callback = f"buy_{resolved_ticker}"
                ignore_callback = f"ignore_{resolved_ticker}"

                bias_emoji = "✅" if bias == "BUY" else "🔴"

                # Build quant badge for the message
                confluence_score = quant_results["confluence"].confluence_score
                quant_badge = ""
                if entry_plan.should_place_order:
                    quant_badge = f"🎯 _Quant Confirmed ({pullback.strategy_name}, Confluence {confluence_score:.0f}/100)_\n"
                elif confluence_score >= 60:
                    quant_badge = f"📊 _Confluence {confluence_score:.0f}/100 ({structure.market_regime.value})_\n"
                else:
                    quant_badge = f"📊 _Quant: {structure.market_regime.value}, Confluence {confluence_score:.0f}/100_\n"

                message = f"🤖 *Oracle Pro Signal*\n"
                message += f"Ticker: `{resolved_ticker}`\n\n"
                message += f"*Bias:* {bias_emoji} {bias}\n"
                message += f"*Entry:* {entry_price if entry_price is not None else 'N/A'}\n"
                message += f"*Target:* {target_price if target_price is not None else 'N/A'}\n"
                message += f"*Stop Loss:* {stop_loss if stop_loss is not None else 'N/A'}\n\n"
                message += f"*Reasoning:* {reason}\n\n"
                message += quant_badge
                message += f"📊 _{data_label or 'N/A'}_\n"
                message += f"⏳ _Expires in {expiry_hours}h_"

                await _send_telegram_message(
                    telegram_bot_token,
                    telegram_chat_id,
                    message,
                    reply_markup={
                        "inline_keyboard": [
                            [
                                {"text": "✅ Beli/Track", "callback_data": buy_callback},
                                {"text": "❌ Abaikan", "callback_data": ignore_callback},
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
    # Run at 09:15 UTC (16:15 WIB for Indo market) and 21:15 UTC (04:15 WIB for US/Global market)
    scheduler.add_job(
        generate_auto_signals,
        "cron",
        hour="9,21",
        minute=15,
        id="auto_signal_scan",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )
    scheduler.start()
    _AUTO_SIGNAL_SCHEDULER = scheduler
    print(
        "Auto Signal Daemon (Pro + Quant) started. "
        "Scanning daily at 16:15 WIB (Indo Close) and 04:15 WIB (US Close)."
    )
