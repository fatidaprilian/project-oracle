import os
import httpx
from datetime import date, datetime, timezone
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from oracle.application.signal_synthesizer import fetch_news_for_ticker, synthesize_signal
from oracle.infrastructure.postgres_repository import (
    init_db,
    save_signal,
    track_symbol,
    ignore_symbol,
    resolve_signal_by_ticker,
    get_signal_prices,
    is_signal_expired_for_ticker,
    close_tracking,
)

app = FastAPI(
    title="Project Oracle API (Stock Pivot)",
    description="Telegram-driven Stock Signal Engine",
    version="0.3.0",
)

TELEGRAM_WEBHOOK_PATH = "/api/v1/webhook/telegram"
_LAST_ANALYSIS_DAY_BY_TICKER: dict[str, date] = {}

allowed_origins = os.getenv("ORACLE_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    if os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() == "true":
        try:
            init_db()
        except Exception as e:
            print(f"Failed to init DB: {e}")

    try:
        from oracle.application.active_tracker import start_daemon
        start_daemon()
    except Exception as e:
        print(f"Failed to start tracking daemon: {e}")

    try:
        from oracle.application.auto_signal_generator import start_auto_signal_daemon
        start_auto_signal_daemon()
    except Exception as e:
        print(f"Failed to start auto signal daemon: {e}")

    try:
        from oracle.application.market_screener import start_daily_broadcast_daemon
        start_daily_broadcast_daemon()
    except Exception as e:
        print(f"Failed to start daily broadcast daemon: {e}")

    try:
        ensure_telegram_webhook()
    except Exception as e:
        print(f"Failed to ensure telegram webhook: {e}")


def _telegram_api_url(bot_token: str, method: str) -> str:
    return f"https://api.telegram.org/bot{bot_token}/{method}"


def _parse_callback_data(callback_data: str) -> tuple[str, str]:
    callback_data = callback_data.strip()
    if "_" not in callback_data:
        return "", ""
    action, ticker = callback_data.split("_", 1)
    return action.strip().lower(), ticker.strip().upper()


def _normalize_ticker(ticker: str) -> str:
    return ticker.strip().upper()


def _format_bias_label(bias: str) -> str:
    if bias == "BUY":
        return "BELI"
    if bias == "SELL":
        return "JUAL"
    return "ABAIKAN"


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


def _was_analyzed_today_in_memory(ticker: str) -> bool:
    normalized_ticker = _normalize_ticker(ticker)
    if not normalized_ticker:
        return False
    return _LAST_ANALYSIS_DAY_BY_TICKER.get(normalized_ticker) == _utc_today()


def _mark_analyzed_today(ticker: str) -> None:
    normalized_ticker = _normalize_ticker(ticker)
    if not normalized_ticker:
        return
    _LAST_ANALYSIS_DAY_BY_TICKER[normalized_ticker] = _utc_today()


def _has_reached_daily_analysis_limit(ticker: str) -> bool:
    normalized_ticker = _normalize_ticker(ticker)
    if not normalized_ticker:
        return False

    postgres_enabled = os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() == "true"
    if postgres_enabled:
        try:
            from oracle.infrastructure.postgres_repository import has_signal_today
            if has_signal_today(normalized_ticker):
                return True
        except Exception as e:
            print(f"Failed DB daily analysis check for {normalized_ticker}: {e}")

    return _was_analyzed_today_in_memory(normalized_ticker)


def ensure_telegram_webhook() -> None:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    webhook_base = os.getenv("ORACLE_TELEGRAM_WEBHOOK_URL", "").strip()
    if not bot_token:
        print("Telegram webhook setup skipped: missing TELEGRAM_BOT_TOKEN")
        return
    if not webhook_base:
        print("Telegram webhook setup skipped: missing ORACLE_TELEGRAM_WEBHOOK_URL")
        return
    if not webhook_base.startswith("https://"):
        print("Telegram webhook setup skipped: ORACLE_TELEGRAM_WEBHOOK_URL must use https")
        return

    webhook_url = (
        webhook_base.rstrip("/")
        if webhook_base.endswith(TELEGRAM_WEBHOOK_PATH)
        else f"{webhook_base.rstrip('/')}{TELEGRAM_WEBHOOK_PATH}"
    )

    payload = {
        "url": webhook_url,
        "allowed_updates": ["callback_query"],
        "drop_pending_updates": False,
    }

    with httpx.Client(timeout=20.0) as client:
        response = client.post(_telegram_api_url(bot_token, "setWebhook"), json=payload)
        response.raise_for_status()
        body = response.json()

    if not body.get("ok", False):
        print(f"Telegram setWebhook failed: {body}")
        return

    print(f"Telegram webhook active: {webhook_url}")


async def _telegram_post(bot_token: str, method: str, payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(_telegram_api_url(bot_token, method), json=payload)
        response.raise_for_status()
        body = response.json()

    if not body.get("ok", False):
        raise RuntimeError(f"Telegram API {method} failed: {body}")
    return body


def _format_duration_window_label(
    estimated_duration_min_days: int | None,
    estimated_duration_max_days: int | None,
) -> str | None:
    if estimated_duration_min_days is None or estimated_duration_max_days is None:
        return None
    if estimated_duration_min_days == estimated_duration_max_days:
        return f"{estimated_duration_min_days} hari bursa"
    return (
        f"{estimated_duration_min_days}-{estimated_duration_max_days} hari bursa"
    )


async def _send_public_buy_signal(
    bot_token: str,
    ticker: str,
    entry: float,
    tp: float,
    sl: float,
    estimated_duration_min_days: int | None = None,
    estimated_duration_max_days: int | None = None,
):
    channel_id = os.getenv("TELEGRAM_PUBLIC_CHANNEL_ID")
    if not channel_id or not bot_token:
        return

    tv_ticker = ticker.replace(".JK", "")
    duration_label = _format_duration_window_label(
        estimated_duration_min_days=estimated_duration_min_days,
        estimated_duration_max_days=estimated_duration_max_days,
    )

    text = (
        f"🚀 *SIGNAL BARU: {ticker}*\n\n"
        f"🎯 Area Beli: {entry:.2f}\n"
        f"💰 Target: {tp:.2f}\n"
        f"🛡️ Stop Loss: {sl:.2f}\n"
    )

    if duration_label is not None:
        text += f"⏱️ Perkiraan Durasi: {duration_label}\n"

    text += (
        "\n"
        "_Durasi di atas adalah estimasi menuju target dalam hari bursa, "
        "bukan janji target tercapai besok._\n\n"
        f"🔗 [Lihat Chart di TradingView](https://www.tradingview.com/chart/?symbol=IDX:{tv_ticker})"
    )

    try:
        await _telegram_post(
            bot_token,
            "sendMessage",
            {
                "chat_id": channel_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
        )
        print(f"Broadcasted {ticker} to public channel.")
    except Exception as e:
        print(f"Failed to send to public channel: {e}")

class HealthResponse(BaseModel):
    status: str
    version: str

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="healthy", version="0.3.0")

class WebhookPayload(BaseModel):
    ticker: str
    signal_type: str
    price: float

@app.post("/api/v1/webhook/tradingview")
async def tradingview_webhook(payload: WebhookPayload):
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    ticker = _normalize_ticker(payload.ticker)

    if not telegram_bot_token or not telegram_chat_id:
        return {"status": "ignored", "reason": "kredensial telegram belum dikonfigurasi"}

    if _has_reached_daily_analysis_limit(ticker):
        return {
            "status": "ignored",
            "reason": "analisis harian untuk ticker ini sudah dilakukan",
            "ticker": ticker,
        }

    # Fetch fundamental news and get AI reasoning
    news = fetch_news_for_ticker(ticker)
    decision = synthesize_signal(ticker, payload.signal_type, payload.price, news)

    # Save to database
    try:
        if os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() == "true":
            save_signal(ticker, payload.signal_type, news, decision['reason'], decision['bias'])
    except Exception as e:
        print(f"Failed to save signal to DB: {e}")

    _mark_analyzed_today(ticker)

    bias_emoji = "✅" if decision["bias"] == "BUY" else "❌"
    bias_label = _format_bias_label(decision["bias"])

    message = f"🚨 *Sinyal Oracle*\n"
    message += f"Saham: `{ticker}`\n"
    message += f"Sinyal teknikal: {payload.signal_type} @ {payload.price}\n\n"
    message += f"*Bias AI:* {bias_emoji} {bias_label}\n"
    message += f"*Alasan:* {decision['reason']}"

    url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json={
                "chat_id": telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "reply_markup": {
                    "inline_keyboard": [
                        [
                            {"text": "✅ Beli", "callback_data": f"buy_{ticker}"},
                            {"text": "❌ Abaikan", "callback_data": f"ignore_{ticker}"}
                        ]
                    ]
                }
            })
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to send telegram message: {e}")
            raise HTTPException(status_code=500, detail="gagal mengirim notifikasi telegram")

    return {"status": "success", "decision": decision}

@app.post("/api/v1/webhook/telegram")
async def telegram_webhook(request: Request):
    payload = await request.json()

    if "callback_query" not in payload:
        return {"status": "ignored", "reason": "bukan callback query"}

    callback_query = payload["callback_query"]
    callback_data = str(callback_query.get("data", ""))
    message = callback_query.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    callback_id = callback_query.get("id")

    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_bot_token:
        return {"status": "error", "reason": "kredensial telegram belum tersedia"}

    action, ticker = _parse_callback_data(callback_data)
    if not action or not ticker:
        return {"status": "ignored", "reason": "callback data tidak valid"}

    # Acknowledge callback as early as possible to stop loading spinner in Telegram UI.
    if callback_id:
        try:
            await _telegram_post(
                telegram_bot_token,
                "answerCallbackQuery",
                {
                    "callback_query_id": callback_id,
                    "text": "Diproses...",
                    "show_alert": False,
                },
            )
        except Exception as e:
            print(f"Failed to acknowledge callback: {e}")

    postgres_enabled = os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() == "true"

    # Fix 2: Check if signal is expired before processing buy/ignore
    if action in ("buy", "ignore") and postgres_enabled:
        try:
            if is_signal_expired_for_ticker(ticker):
                status_text = f"⏳ Signal untuk {ticker} sudah kadaluarsa."
                if chat_id is not None:
                    try:
                        await _telegram_post(
                            telegram_bot_token,
                            "sendMessage",
                            {"chat_id": chat_id, "text": status_text},
                        )
                    except Exception:
                        pass
                # Clear inline keyboard
                if chat_id is not None and message_id is not None:
                    try:
                        await _telegram_post(
                            telegram_bot_token,
                            "editMessageReplyMarkup",
                            {
                                "chat_id": chat_id,
                                "message_id": message_id,
                                "reply_markup": {"inline_keyboard": []},
                            },
                        )
                    except Exception:
                        pass
                return {"status": "expired", "action": action, "ticker": ticker}
        except Exception as e:
            print(f"Failed expiry check for {ticker}: {e}")

    status_text = "Aksi tidak dikenali."
    try:
        if action == "buy":
            if postgres_enabled:
                # Get signal prices for the tracking entry
                prices = get_signal_prices(ticker)
                if not prices:
                    # Resolve and get prices from current signal
                    resolve_signal_by_ticker(ticker, "BUY")
                    prices = get_signal_prices(ticker)

                entry_price = prices.get("entry_price") if prices else None
                target_price = prices.get("target_price") if prices else None
                stop_loss_price = prices.get("stop_loss") if prices else None
                estimated_duration_min_days = (
                    prices.get("estimated_duration_min_days") if prices else None
                )
                estimated_duration_max_days = (
                    prices.get("estimated_duration_max_days") if prices else None
                )

                # First resolve, then get the signal_id
                if not prices:
                    resolve_signal_by_ticker(ticker, "BUY")

                track_symbol(
                    ticker,
                    entry_price=entry_price,
                    target_price=target_price,
                    stop_loss=stop_loss_price,
                    estimated_duration_min_days=estimated_duration_min_days,
                    estimated_duration_max_days=estimated_duration_max_days,
                )
                
                if entry_price is not None and target_price is not None and stop_loss_price is not None:
                    await _send_public_buy_signal(
                        telegram_bot_token,
                        ticker,
                        entry_price,
                        target_price,
                        stop_loss_price,
                        estimated_duration_min_days=estimated_duration_min_days,
                        estimated_duration_max_days=estimated_duration_max_days,
                    )
                    
            status_text = f"Tracking aktif untuk {ticker}."

        elif action == "ignore":
            if postgres_enabled:
                resolve_signal_by_ticker(ticker, "IGNORE")
                ignore_symbol(ticker)
            status_text = f"{ticker} dimute selama 3 hari."

        elif action == "sell":
            if postgres_enabled:
                close_tracking(ticker)
            status_text = f"Posisi {ticker} ditutup. Cooldown 3 hari aktif."

        elif action == "keep":
            status_text = f"Tetap tahan {ticker}. Monitoring lanjut berjalan."

    except Exception as e:
        print(f"DB Error on Callback: {e}")
        status_text = f"Aksi untuk {ticker} gagal disimpan."

    if chat_id is not None and message_id is not None:
        try:
            await _telegram_post(
                telegram_bot_token,
                "editMessageReplyMarkup",
                {
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "reply_markup": {"inline_keyboard": []},
                },
            )
        except Exception as e:
            print(f"Failed to clear inline keyboard: {e}")

    if chat_id is not None:
        try:
            await _telegram_post(
                telegram_bot_token,
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": f"✅ {status_text}",
                },
            )
        except Exception as e:
            print(f"Failed to send callback confirmation message: {e}")

    return {"status": "success", "action": action, "ticker": ticker}

@app.get("/api/v1/dashboard/signals")
async def get_dashboard_signals_endpoint():
    try:
        from oracle.infrastructure.postgres_repository import get_dashboard_signals as load_dashboard_signals
        if os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() != "true":
            return {"signals": []}

        signals = load_dashboard_signals(limit=50, unresolved_expiry_hours=24)
        return {"signals": signals}
    except Exception as e:
        print(f"Error fetching signals: {e}")
        return {"signals": []}


# Fix 6: Portfolio endpoint
@app.get("/api/v1/dashboard/portfolio")
async def get_portfolio_endpoint():
    try:
        from oracle.infrastructure.postgres_repository import get_portfolio
        if os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() != "true":
            return {"portfolio": []}
        return {"portfolio": get_portfolio()}
    except Exception as e:
        print(f"Error fetching portfolio: {e}")
        return {"portfolio": []}


@app.get("/api/v1/dashboard/anomalies")
async def get_anomalies_endpoint():
    try:
        from oracle.infrastructure.postgres_repository import get_daily_anomalies
        if os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() != "true":
            return {"anomalies": []}
        return {"anomalies": get_daily_anomalies()}
    except Exception as e:
        print(f"Error fetching anomalies: {e}")
        return {"anomalies": []}


# Fix 6: Signal history endpoint
@app.get("/api/v1/dashboard/history")
async def get_history_endpoint():
    try:
        from oracle.infrastructure.postgres_repository import get_signal_history
        if os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() != "true":
            return {"history": []}
        return {"history": get_signal_history(limit=50)}
    except Exception as e:
        print(f"Error fetching history: {e}")
        return {"history": []}


class DashboardActionPayload(BaseModel):
    ticker: str
    action: str

@app.post("/api/v1/dashboard/action")
async def dashboard_action(payload: DashboardActionPayload):
    try:
        from oracle.infrastructure.postgres_repository import (
            track_symbol,
            ignore_symbol,
            close_tracking,
            resolve_signal_by_ticker,
            get_signal_prices,
        )
        postgres_enabled = os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() == "true"
        entry = None
        target = None
        sl = None
        estimated_duration_min_days = None
        estimated_duration_max_days = None

        if payload.action == "buy":
            if postgres_enabled:
                resolve_signal_by_ticker(payload.ticker, "BUY")
                prices = get_signal_prices(payload.ticker)
                entry = prices.get("entry_price") if prices else None
                target = prices.get("target_price") if prices else None
                sl = prices.get("stop_loss") if prices else None
                estimated_duration_min_days = (
                    prices.get("estimated_duration_min_days") if prices else None
                )
                estimated_duration_max_days = (
                    prices.get("estimated_duration_max_days") if prices else None
                )
                track_symbol(
                    payload.ticker,
                    entry_price=entry,
                    target_price=target,
                    stop_loss=sl,
                    estimated_duration_min_days=estimated_duration_min_days,
                    estimated_duration_max_days=estimated_duration_max_days,
                )
            message = f"*[🟢 Tracking aktif untuk {payload.ticker}]* (dipicu dari dashboard)"

        elif payload.action == "ignore":
            if postgres_enabled:
                resolve_signal_by_ticker(payload.ticker, "IGNORE")
                ignore_symbol(payload.ticker)
            message = f"*[🔴 {payload.ticker} dimute selama 3 hari]* (dipicu dari dashboard)"

        elif payload.action == "sell":
            pnl = None
            if postgres_enabled:
                pnl = close_tracking(payload.ticker)
            
            if pnl is not None:
                status = (
                    "🏆 UNTUNG"
                    if pnl > 0
                    else ("🛑 RUGI" if pnl < 0 else "⚪ IMPAS")
                )
                message = (
                    f"*[{status}: {pnl:+.2f}%] Posisi {payload.ticker} ditutup* "
                    "(dipicu dari dashboard)"
                )
            else:
                message = (
                    f"*[🔻 Posisi {payload.ticker} ditutup]* "
                    "(dipicu dari dashboard)"
                )

        else:
            raise HTTPException(status_code=400, detail="aksi tidak valid")

        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if telegram_bot_token and telegram_chat_id:
            url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
            async with httpx.AsyncClient() as client:
                await client.post(url, json={
                    "chat_id": telegram_chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                })
                
            if payload.action == "buy" and entry is not None and target is not None and sl is not None:
                await _send_public_buy_signal(
                    telegram_bot_token,
                    payload.ticker,
                    entry,
                    target,
                    sl,
                    estimated_duration_min_days=estimated_duration_min_days,
                    estimated_duration_max_days=estimated_duration_max_days,
                )

        return {"status": "success", "action": payload.action, "ticker": payload.ticker}
    except Exception as e:
        print(f"Error on dashboard action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/dashboard/watchlist")
async def get_watchlist_api():
    try:
        from oracle.infrastructure.postgres_repository import get_watchlist
        if os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() != "true":
            return {"watchlist": []}
        return {"watchlist": get_watchlist()}
    except Exception as e:
        print(f"Error fetching watchlist: {e}")
        return {"watchlist": []}

class WatchlistPayload(BaseModel):
    ticker: str

@app.post("/api/v1/dashboard/watchlist")
async def add_watchlist_api(payload: WatchlistPayload):
    try:
        from oracle.infrastructure.postgres_repository import add_to_watchlist
        if os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() != "true":
            raise HTTPException(status_code=400, detail="Postgres tidak aktif")
        add_to_watchlist(payload.ticker.upper())
        return {"status": "success", "ticker": payload.ticker.upper()}
    except Exception as e:
        print(f"Error adding to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/dashboard/watchlist/{ticker}")
async def remove_watchlist_api(ticker: str):
    try:
        from oracle.infrastructure.postgres_repository import remove_from_watchlist
        if os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() != "true":
            raise HTTPException(status_code=400, detail="Postgres tidak aktif")
        remove_from_watchlist(ticker.upper())
        return {"status": "success", "ticker": ticker.upper()}
    except Exception as e:
        print(f"Error removing from watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/dashboard/stats")
async def get_stats_endpoint():
    try:
        from oracle.infrastructure.postgres_repository import get_trading_stats
        if os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() != "true":
            return {"total": 0, "wins": 0, "losses": 0, "win_rate": 0, "avg_pnl": 0}
        return get_trading_stats()
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return {"total": 0, "wins": 0, "losses": 0, "win_rate": 0, "avg_pnl": 0}

@app.post("/api/v1/admin/scan-now")
async def trigger_scan_api():
    try:
        from oracle.application.auto_signal_generator import generate_auto_signals
        import asyncio
        asyncio.create_task(generate_auto_signals())
        return {
            "status": "success",
            "message": "Scan dijalankan di background. Cek Telegram atau dashboard dalam beberapa menit.",
        }
    except Exception as e:
        print(f"Error triggering scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/admin/monitor-now")
async def trigger_monitor_api():
    try:
        from oracle.application.active_tracker import run_active_tracker_check
        import asyncio
        asyncio.create_task(run_active_tracker_check())
        return {
            "status": "success",
            "message": "Pengecekan monitoring dijalankan di background.",
        }
    except Exception as e:
        print(f"Error triggering monitor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
