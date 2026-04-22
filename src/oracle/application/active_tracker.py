import os
import asyncio
import httpx
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from oracle.infrastructure.postgres_repository import get_active_trackings, update_last_checked, close_tracking
from oracle.application.signal_synthesizer import fetch_news_for_ticker
from google import genai
from pydantic import BaseModel, Field

class TrackerDecision(BaseModel):
    action: str = Field(description="Must be 'HOLD' or 'ALERT'")
    reason: str = Field(description="Short reason why, max 2 sentences")

async def run_tracking_daemon():
    print("Running Active Tracking Daemon...")
    trackings = get_active_trackings()
    if not trackings:
        print("No active trackings found.")
        return

    api_key = os.getenv("ORACLE_AI_ANALYST_API_KEY")
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not api_key or not telegram_bot_token or not telegram_chat_id:
        print("Missing credentials for tracking daemon")
        return
        
    client = genai.Client(api_key=api_key)

    for item in trackings:
        ticker = item["ticker"]
        tracking_id = item["id"]
        
        # 1. Fetch latest news
        news = fetch_news_for_ticker(ticker, max_headlines=5)
        if "No recent news" in news:
            update_last_checked(tracking_id)
            continue
            
        # 2. Ask Gemini if news is severely bad
        prompt = f"""
You are the Oracle Risk Daemon. You are actively tracking {ticker}.
Recent Headlines:
{news}

If there is SEVERELY BAD news (bankruptcy, SEC probe, massive miss, CEO fired, etc) that warrants an immediate panic sell, output 'ALERT'.
Otherwise, if news is normal, mildly bad, or positive, output 'HOLD'.
"""
        try:
            response = client.models.generate_content(
                model='gemini-2.5-pro',
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': TrackerDecision,
                    'temperature': 0.1,
                },
            )
            result = json.loads(response.text)
            
            # 3. Alert if necessary
            if result["action"] == "ALERT":
                message = f"⚠️ *EMERGENCY ALERT: {ticker}*\n\n"
                message += f"*Bad News Detected:*\n{result['reason']}\n\n"
                message += f"What do you want to do?"
                
                url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
                async with httpx.AsyncClient() as http_client:
                    await http_client.post(url, json={
                        "chat_id": telegram_chat_id,
                        "text": message,
                        "parse_mode": "Markdown",
                        "reply_markup": {
                            "inline_keyboard": [
                                [
                                    {"text": "❌ Lepas/Jual", "callback_data": f"ignore_{ticker}"},
                                    {"text": "👀 Tahan Dulu", "callback_data": f"keep_{ticker}"}
                                ]
                            ]
                        }
                    })
            
            update_last_checked(tracking_id)
        except Exception as e:
            print(f"Failed tracking check for {ticker}: {e}")

def start_daemon():
    scheduler = AsyncIOScheduler()
    interval_minutes = int(os.getenv("ORACLE_SCHEDULER_INTERVAL_MINUTES", "60"))
    scheduler.add_job(run_tracking_daemon, 'interval', minutes=interval_minutes)
    scheduler.start()
    print(f"Tracking Daemon started. Running every {interval_minutes} minutes.")
