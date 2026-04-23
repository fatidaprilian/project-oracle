import os
import asyncio
import httpx
import json
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from oracle.infrastructure.postgres_repository import (
    get_active_trackings,
    update_tracking_price,
    update_last_checked,
    close_tracking,
    save_tracking_alert,
)
from oracle.application.signal_synthesizer import fetch_news_for_ticker
from google import genai
from pydantic import BaseModel, Field


class TrackerDecision(BaseModel):
    action: str = Field(description="Must be 'HOLD' or 'ALERT'")
    reason: str = Field(description="Short reason why, max 2 sentences")


def _load_current_price(yf_module: object, ticker: str) -> float | None:
    """Fetch the latest price for a ticker from yfinance."""
    try:
        stock = yf_module.Ticker(ticker)
        hist = stock.history(period="5d")
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception as e:
        print(f"Failed to fetch price for {ticker}: {e}")
        return None


async def _send_telegram_alert(
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
        print(f"Failed to send telegram alert: {e}")
        return False


async def run_tracking_daemon():
    print("Running Active Tracking Daemon...")
    trackings = get_active_trackings()
    if not trackings:
        print("No active trackings found.")
        return

    api_key = os.getenv("ORACLE_AI_ANALYST_API_KEY")
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    telegram_public_channel_id = os.getenv("TELEGRAM_PUBLIC_CHANNEL_ID")

    if not api_key or not telegram_bot_token or not telegram_chat_id:
        print("Missing credentials for tracking daemon")
        return

    try:
        import yfinance as yf
    except Exception as e:
        print(f"Missing dependency yfinance for Tracking Daemon: {e}")
        return

    logging.getLogger("yfinance").setLevel(logging.CRITICAL)

    client = genai.Client(api_key=api_key)

    for item in trackings:
        ticker = item["ticker"]
        tracking_id = item["id"]
        entry_price = item.get("entry_price")
        target_price = item.get("target_price")
        stop_loss = item.get("stop_loss")

        # --- Fix 7: Price-Based Monitoring ---
        current_price = _load_current_price(yf, ticker)
        if current_price is not None:
            # Calculate PnL
            pnl_percent = 0.0
            if entry_price and entry_price > 0:
                pnl_percent = round(
                    ((current_price - entry_price) / entry_price) * 100, 2
                )

            # Update price in database for web monitoring
            try:
                update_tracking_price(tracking_id, current_price, pnl_percent)
            except Exception as e:
                print(f"Failed to update price for {ticker}: {e}")

            now_wib = __import__("datetime").datetime.now(__import__("datetime").timezone.utc) + __import__("datetime").timedelta(hours=7)
            time_str = now_wib.strftime("%d %b %Y, %H:%M WIB")

            # Check target reached
            if target_price and current_price >= target_price:
                base_message = (
                    f"🎯 *TARGET REACHED: {ticker}*\n\n"
                    f"*Current Price:* {current_price:.2f}\n"
                    f"*Target Price:* {target_price:.2f}\n"
                    f"*Entry Price:* {entry_price:.2f if entry_price else 'N/A'}\n"
                    f"*PnL:* {pnl_percent:+.2f}%\n"
                    f"*Waktu:* {time_str}"
                )
                
                private_message = base_message + "\n\n✅ Posisi otomatis ditutup (Auto-Sell)."
                await _send_telegram_alert(telegram_bot_token, telegram_chat_id, private_message)
                
                if telegram_public_channel_id:
                    await _send_telegram_alert(telegram_bot_token, telegram_public_channel_id, base_message)

                try:
                    close_tracking(ticker)
                except Exception as e:
                    print(f"Failed to close tracking for {ticker}: {e}")
                continue

            # Check stop loss hit
            if stop_loss and current_price <= stop_loss:
                base_message = (
                    f"🛑 *STOP LOSS HIT: {ticker}*\n\n"
                    f"*Current Price:* {current_price:.2f}\n"
                    f"*Stop Loss:* {stop_loss:.2f}\n"
                    f"*Entry Price:* {entry_price:.2f if entry_price else 'N/A'}\n"
                    f"*PnL:* {pnl_percent:+.2f}%\n"
                    f"*Waktu:* {time_str}"
                )
                
                private_message = base_message + "\n\n❌ Posisi otomatis ditutup (Auto-Cutloss)."
                await _send_telegram_alert(telegram_bot_token, telegram_chat_id, private_message)
                
                if telegram_public_channel_id:
                    await _send_telegram_alert(telegram_bot_token, telegram_public_channel_id, base_message)

                try:
                    close_tracking(ticker)
                except Exception as e:
                    print(f"Failed to close tracking for {ticker}: {e}")
                continue

        # --- Fix 5: News-Based Sell Signal (existing + enhanced) ---
        news = fetch_news_for_ticker(ticker, max_headlines=5)
        if "No recent news" in news:
            update_last_checked(tracking_id)
            continue

        # Ask Gemini if news is severely bad
        price_context = ""
        if current_price is not None:
            price_context = f"\nCurrent Price: {current_price:.2f}"
            if entry_price:
                price_context += f"\nEntry Price: {entry_price:.2f}"
                pnl = ((current_price - entry_price) / entry_price) * 100
                price_context += f"\nUnrealized PnL: {pnl:+.2f}%"

        prompt = f"""
You are the Oracle Risk Daemon. You are actively tracking {ticker}.
{price_context}

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

            # Alert if necessary
            if result["action"] == "ALERT":
                message = f"⚠️ *EMERGENCY ALERT: {ticker}*\n\n"
                message += f"*Bad News Detected:*\n{result['reason']}\n\n"
                if current_price is not None:
                    message += f"*Current Price:* {current_price:.2f}\n"
                    if entry_price:
                        pnl = ((current_price - entry_price) / entry_price) * 100
                        message += f"*PnL:* {pnl:+.2f}%\n"
                message += f"\nApa yang ingin dilakukan?"

                await _send_telegram_alert(
                    telegram_bot_token,
                    telegram_chat_id,
                    message,
                    reply_markup={
                        "inline_keyboard": [
                            [
                                {"text": "❌ Lepas/Jual", "callback_data": f"sell_{ticker}"},
                                {"text": "👀 Tahan Dulu", "callback_data": f"keep_{ticker}"},
                            ]
                        ]
                    },
                )
                try:
                    save_tracking_alert(tracking_id, "NEWS_ALERT", result["reason"])
                except Exception:
                    pass

            update_last_checked(tracking_id)
        except Exception as e:
            print(f"Failed tracking check for {ticker}: {e}")

        await asyncio.sleep(2)


def start_daemon():
    scheduler = AsyncIOScheduler()
    interval_minutes = int(os.getenv("ORACLE_SCHEDULER_INTERVAL_MINUTES", "60"))
    from datetime import datetime, timezone
    scheduler.add_job(
        run_tracking_daemon,
        'interval',
        minutes=interval_minutes,
        id="active_tracking_daemon",
        next_run_time=datetime.now(timezone.utc),
        max_instances=1,
        coalesce=True,
        misfire_grace_time=120,
    )
    scheduler.start()
    print(f"Tracking Daemon started. Running every {interval_minutes} minutes.")
