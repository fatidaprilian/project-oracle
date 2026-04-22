import os
import asyncio
import httpx
import json
import yfinance as yf
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from oracle.application.signal_synthesizer import fetch_news_for_ticker
from oracle.infrastructure.postgres_repository import save_signal, get_watchlist
from google import genai
from pydantic import BaseModel, Field

class AutoSignalDecision(BaseModel):
    bias: str = Field(description="Must be BUY, SELL, or IGNORE")
    reason: str = Field(description="Max 2 sentences of reasoning")
    entry_price: float = Field(description="Suggested entry price", default=0.0)
    target_price: float = Field(description="Suggested take profit price", default=0.0)
    stop_loss: float = Field(description="Suggested stop loss price", default=0.0)

async def generate_auto_signals():
    print("Running Auto Signal Generator Daemon (Pro 2026)...")
    
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    api_key = os.getenv("ORACLE_AI_ANALYST_API_KEY")
    
    if not telegram_bot_token or not telegram_chat_id or not api_key:
        print("Missing credentials for Auto Signal Generator")
        return
        
    client = genai.Client(api_key=api_key)

    # 1. Fetch Dynamic Watchlist
    try:
        watchlist = get_watchlist()
    except Exception as e:
        print(f"Failed to fetch watchlist from DB: {e}")
        watchlist = ["AAPL", "NVDA", "TSLA", "BBCA.JK", "GOTO.JK", "AMZN"]
        
    if not watchlist:
        watchlist = ["AAPL", "NVDA", "TSLA", "BBCA.JK", "GOTO.JK", "AMZN"]

    for ticker in watchlist:
        print(f"Analyzing {ticker} for auto-signal...")
        
        # 2. Fetch Fundamental News
        news = fetch_news_for_ticker(ticker, max_headlines=5)
        
        # 3. Fetch Technical Data via yfinance
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1mo")
            if hist.empty:
                print(f"No price data for {ticker}")
                continue
                
            current_price = hist['Close'].iloc[-1]
            high_30d = hist['High'].max()
            low_30d = hist['Low'].min()
            volume = hist['Volume'].iloc[-1]
            
            technical_context = f"Current Price: {current_price:.2f}\n"
            technical_context += f"30-Day High (Resistance): {high_30d:.2f}\n"
            technical_context += f"30-Day Low (Support): {low_30d:.2f}\n"
            technical_context += f"Latest Volume: {volume}"
        except Exception as e:
            print(f"Failed to fetch yfinance data for {ticker}: {e}")
            continue

        # 4. Synthesize with Gemini
        prompt = f"""
You are Oracle Pro 2026, an elite quantitative analyst.
Analyze the following stock: {ticker}

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
            
            # 5. Push if strong bias
            if decision["bias"] in ["BUY", "SELL"]:
                # Save to DB
                if os.getenv("ORACLE_ENABLE_POSTGRES", "false").lower() == "true":
                    try:
                        save_signal(
                            ticker=ticker, 
                            signal_type="AI_PRO_SCAN", 
                            news=news, 
                            reasoning=decision['reason'], 
                            bias=decision['bias'],
                            entry=decision.get('entry_price'),
                            tp=decision.get('target_price'),
                            sl=decision.get('stop_loss')
                        )
                    except Exception as e:
                        print(f"Failed to save auto signal to DB: {e}")

                # Send to Telegram
                bias_emoji = "✅" if decision["bias"] == "BUY" else "🔴"
                message = f"🤖 *Oracle Pro Signal*\n"
                message += f"Ticker: `{ticker}`\n\n"
                message += f"*Bias:* {bias_emoji} {decision['bias']}\n"
                message += f"*Entry:* {decision.get('entry_price', 'N/A')}\n"
                message += f"*Target:* {decision.get('target_price', 'N/A')}\n"
                message += f"*Stop Loss:* {decision.get('stop_loss', 'N/A')}\n\n"
                message += f"*Reasoning:* {decision['reason']}"
                
                url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
                async with httpx.AsyncClient() as http_client:
                    await http_client.post(url, json={
                        "chat_id": telegram_chat_id,
                        "text": message,
                        "parse_mode": "Markdown",
                        "reply_markup": {
                            "inline_keyboard": [
                                [
                                    {"text": "✅ Beli/Track", "callback_data": f"buy_{ticker}"},
                                    {"text": "❌ Abaikan", "callback_data": f"ignore_{ticker}"}
                                ]
                            ]
                        }
                    })
        except Exception as e:
            print(f"Failed Gemini analysis for {ticker}: {e}")
            
        await asyncio.sleep(4)

def start_auto_signal_daemon():
    scheduler = AsyncIOScheduler()
    interval_hours = int(os.getenv("ORACLE_AUTO_SIGNAL_HOURS", "2"))
    scheduler.add_job(generate_auto_signals, 'interval', hours=interval_hours)
    scheduler.start()
    print(f"Auto Signal Daemon (Pro) started. Scanning every {interval_hours} hours.")
