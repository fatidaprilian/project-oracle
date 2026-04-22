import os
import asyncio
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from oracle.application.signal_synthesizer import fetch_news_for_ticker, synthesize_signal
from oracle.infrastructure.postgres_repository import save_signal

# Mix of international and local Indonesian stocks
DEFAULT_WATCHLIST = ["AAPL", "NVDA", "TSLA", "BBCA.JK", "GOTO.JK", "AMZN"]

async def generate_auto_signals():
    print("Running Auto Signal Generator Daemon...")
    
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not telegram_bot_token or not telegram_chat_id:
        print("Missing Telegram credentials for Auto Signal Generator")
        return

    for ticker in DEFAULT_WATCHLIST:
        print(f"Analyzing {ticker} for auto-signal...")
        
        # 1. Fetch News
        news = fetch_news_for_ticker(ticker, max_headlines=5)
        if "No recent news" in news:
            continue
            
        # 2. Synthesize using our existing Gemini logic
        # We pass a dummy "AUTO_SCAN" as technical signal since we are relying purely on news
        decision = synthesize_signal(ticker, "AUTO_SCAN_FUNDAMENTAL", 0.0, news)
        
        # 3. Only push to telegram/web if it has a strong bias (not just ignoring everything)
        # We'll push if the reasoning sounds like a solid BUY.
        if decision["bias"] == "BUY":
            # Save to DB so it appears on Web Dashboard
            if os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() == "true":
                try:
                    save_signal(ticker, "AUTO_SCAN_FUNDAMENTAL", news, decision['reason'], decision['bias'])
                except Exception as e:
                    print(f"Failed to save auto signal to DB: {e}")

            # Send to Telegram
            bias_emoji = "✅" if decision["bias"] == "BUY" else "❌"
            message = f"🤖 *Auto Oracle Signal*\n"
            message += f"Ticker: `{ticker}`\n"
            message += f"Type: Periodic Scan\n\n"
            message += f"*AI Bias:* {bias_emoji} {decision['bias']}\n"
            message += f"*Reasoning:* {decision['reason']}"
            
            url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
            async with httpx.AsyncClient() as client:
                try:
                    await client.post(url, json={
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
                except Exception as e:
                    print(f"Failed to send telegram auto-signal: {e}")
        
        # Sleep slightly to avoid rate-limiting from Gemini API
        await asyncio.sleep(3)

def start_auto_signal_daemon():
    scheduler = AsyncIOScheduler()
    # Run every 2 hours
    interval_hours = int(os.getenv("ORACLE_AUTO_SIGNAL_HOURS", "2"))
    scheduler.add_job(generate_auto_signals, 'interval', hours=interval_hours)
    scheduler.start()
    print(f"Auto Signal Daemon started. Scanning every {interval_hours} hours.")
