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
    callback_data = callback_query.get("data", "")
    message = callback_query.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    callback_id = callback_query.get("id")
    
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_bot_token:
        return {"status": "error", "reason": "telegram credentials missing"}

    new_text = message.get("text", "") + "\n\n"
    
    try:
        if callback_data.startswith("buy_"):
            ticker = callback_data.split("_")[1]
            if os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() == "true":
                track_symbol(ticker)
            new_text += f"*[🟢 Tracking Active for {ticker}]*"
        elif callback_data.startswith("ignore_"):
            ticker = callback_data.split("_")[1]
            if os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() == "true":
                ignore_symbol(ticker)
            new_text += f"*[🔴 Muted {ticker} for 3 days]*"
    except Exception as e:
        print(f"DB Error on Callback: {e}")

    # Edit the message to remove buttons and show state
    edit_url = f"https://api.telegram.org/bot{telegram_bot_token}/editMessageText"
    answer_url = f"https://api.telegram.org/bot{telegram_bot_token}/answerCallbackQuery"
    
    async with httpx.AsyncClient() as client:
        # Edit Message
        await client.post(edit_url, json={
            "chat_id": chat_id,
            "message_id": message_id,
            "text": new_text,
            "parse_mode": "Markdown"
        })
        # Acknowledge callback to remove loading state on button
        await client.post(answer_url, json={
            "callback_query_id": callback_id
        })

    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
