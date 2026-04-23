import os
import httpx
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from oracle.application.signal_synthesizer import fetch_news_for_ticker, synthesize_signal
from oracle.infrastructure.postgres_repository import init_db, save_signal, track_symbol, ignore_symbol

app = FastAPI(
    title="Project Oracle API (Stock Pivot)",
    description="Telegram-driven Stock Signal Engine",
    version="0.2.0",
)

TELEGRAM_WEBHOOK_PATH = "/api/v1/webhook/telegram"

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

class HealthResponse(BaseModel):
    status: str
    version: str

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="healthy", version="0.2.0")

class WebhookPayload(BaseModel):
    ticker: str
    signal_type: str
    price: float

@app.post("/api/v1/webhook/tradingview")
async def tradingview_webhook(payload: WebhookPayload):
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not telegram_bot_token or not telegram_chat_id:
        return {"status": "ignored", "reason": "telegram credentials not configured"}

    # Fetch fundamental news and get AI reasoning
    news = fetch_news_for_ticker(payload.ticker)
    decision = synthesize_signal(payload.ticker, payload.signal_type, payload.price, news)
    
    # Save to database
    try:
        if os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() == "true":
            save_signal(payload.ticker, payload.signal_type, news, decision['reason'], decision['bias'])
    except Exception as e:
        print(f"Failed to save signal to DB: {e}")

    bias_emoji = "✅" if decision["bias"] == "BUY" else "❌"

    message = f"🚨 *Oracle Signal*\n"
    message += f"Ticker: `{payload.ticker}`\n"
    message += f"Technical: {payload.signal_type} @ {payload.price}\n\n"
    message += f"*AI Bias:* {bias_emoji} {decision['bias']}\n"
    message += f"*Reasoning:* {decision['reason']}"

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
                            {"text": "✅ Beli", "callback_data": f"buy_{payload.ticker}"},
                            {"text": "❌ Abaikan", "callback_data": f"ignore_{payload.ticker}"}
                        ]
                    ]
                }
            })
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to send telegram message: {e}")
            raise HTTPException(status_code=500, detail="Failed to send telegram notification")

    return {"status": "success", "decision": decision}

@app.post("/api/v1/webhook/telegram")
async def telegram_webhook(request: Request):
    payload = await request.json()
    
    if "callback_query" not in payload:
        return {"status": "ignored", "reason": "Not a callback query"}

    callback_query = payload["callback_query"]
    callback_data = str(callback_query.get("data", ""))
    message = callback_query.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    callback_id = callback_query.get("id")
    
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_bot_token:
        return {"status": "error", "reason": "telegram credentials missing"}

    action, ticker = _parse_callback_data(callback_data)
    if not action or not ticker:
        return {"status": "ignored", "reason": "invalid callback data"}

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

    status_text = "Aksi tidak dikenali."
    try:
        if action == "buy":
            if os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() == "true":
                track_symbol(ticker)
            status_text = f"Tracking aktif untuk {ticker}."
        elif action == "ignore":
            if os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() == "true":
                ignore_symbol(ticker)
            status_text = f"{ticker} dimute selama 3 hari."
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
async def get_dashboard_signals():
    try:
        from oracle.infrastructure.postgres_repository import get_recent_signals, get_tracking_status
        if os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() != "true":
            return {"signals": []}
            
        signals = get_recent_signals(50)
        # enrich with status
        for s in signals:
            s["status"] = get_tracking_status(s["ticker"])
            
        return {"signals": signals}
    except Exception as e:
        print(f"Error fetching signals: {e}")
        return {"signals": []}

class DashboardActionPayload(BaseModel):
    ticker: str
    action: str

@app.post("/api/v1/dashboard/action")
async def dashboard_action(payload: DashboardActionPayload):
    try:
        from oracle.infrastructure.postgres_repository import track_symbol, ignore_symbol
        if payload.action == "buy":
            track_symbol(payload.ticker)
            message = f"*[🟢 Tracking Active for {payload.ticker}]* (Triggered from Web)"
        elif payload.action == "ignore":
            ignore_symbol(payload.ticker)
            message = f"*[🔴 Muted {payload.ticker} for 3 days]* (Triggered from Web)"
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
            
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
            raise HTTPException(status_code=400, detail="Postgres is not enabled")
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
            raise HTTPException(status_code=400, detail="Postgres is not enabled")
        remove_from_watchlist(ticker.upper())
        return {"status": "success", "ticker": ticker.upper()}
    except Exception as e:
        print(f"Error removing from watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
