import os
import httpx
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from oracle.application.signal_synthesizer import fetch_news_for_ticker, synthesize_signal

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
