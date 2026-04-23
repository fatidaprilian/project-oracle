import httpx
import asyncio
from datetime import datetime, timezone, timedelta
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler

def fetch_anomalous_stocks() -> list[str]:
    """
    Fetch Indonesian stocks from TradingView screener that have unusual volume.
    Returns a list of ticker symbols (e.g. ['WBSA.JK', 'GOTO.JK']).
    """
    url = "https://scanner.tradingview.com/indonesia/scan"
    
    # We want stocks where current volume is at least 2x the 10-day average volume
    # and the price is actually going up (change > 0).
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock"]},
            {"left": "change", "operation": "greater", "right": 0},
            {"left": "volume", "operation": "nempty"},
            {"left": "average_volume_10d_calc", "operation": "nempty"},
        ],
        "options": {"lang": "en"},
        "markets": ["indonesia"],
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": ["name", "close", "volume", "average_volume_10d_calc", "change"],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [0, 50]  # Check top 50 by volume
    }

    try:
        response = httpx.post(url, json=payload, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        anomalies_with_ratio = []
        for item in data.get("data", []):
            d = item.get("d", [])
            if len(d) >= 5:
                ticker_raw = d[0]  # e.g., 'IDX:WBSA'
                # Remove the 'IDX:' prefix if it exists
                ticker = ticker_raw.split(':')[-1] if ':' in ticker_raw else ticker_raw
                
                close_price = d[1]
                volume = d[2]
                avg_vol_10d = d[3]
                change_pct = d[4]
                
                # Check for Volume Anomaly (Volume > 2.5x of 10-day average)
                # and ensure it's not a penny stock with tiny volume
                if avg_vol_10d > 100000 and volume > (avg_vol_10d * 2.5):
                    ratio = volume / avg_vol_10d
                    yf_ticker = f"{ticker}.JK"
                    anomalies_with_ratio.append((yf_ticker, ratio))
                    
        # Sort by highest volume spike ratio
        anomalies_with_ratio.sort(key=lambda x: x[1], reverse=True)
        
        # Take ONLY the TOP 5 best anomalies to avoid double/spam
        anomalies = [x[0] for x in anomalies_with_ratio[:5]]
        
        print(f"[Market Screener] Found {len(anomalies)} top anomalies.")
        return anomalies
    except Exception as e:
        print(f"[Market Screener] Error fetching screener data: {e}")
        return []

def run_market_screener() -> list[str]:
    print("[Market Screener] Scanning IDX for volume anomalies...")
    anomalies = fetch_anomalous_stocks()
    
    if not anomalies:
        return []
        
    try:
        from oracle.infrastructure.postgres_repository import save_daily_anomalies
        save_daily_anomalies(anomalies)
    except Exception as e:
        print(f"[Market Screener] Failed to save daily anomalies to DB: {e}")
        
    return anomalies

async def daily_telegram_broadcast():
    try:
        from oracle.infrastructure.postgres_repository import get_daily_anomalies
        anomalies = get_daily_anomalies()
        if not anomalies:
            print("[Daily Broadcast] No anomalies found for today.")
            return

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        channel_id = os.getenv("TELEGRAM_PUBLIC_CHANNEL_ID")
        
        if not bot_token or not channel_id:
            print("[Daily Broadcast] Missing Telegram credentials.")
            return

        # Format date for Indonesia (WIB UTC+7)
        now_wib = datetime.now(timezone.utc) + timedelta(hours=7)
        days_id = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        months_id = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        
        day_str = days_id[now_wib.weekday()]
        month_str = months_id[now_wib.month - 1]
        date_str = f"{day_str}, {now_wib.day} {month_str} {now_wib.year}"

        ticker_list = "\n".join([f"• {t.replace('.JK', '')}" for t in anomalies])
        
        message = (
            f"🔍 *POTENSI SAHAM BESOK*\n"
            f"_{date_str}_\n\n"
            f"Berdasarkan hasil _Oracle Volume Screener_ sore ini, berikut adalah saham-saham anomali yang masuk radar pantauan AI untuk besok:\n\n"
            f"{ticker_list}\n\n"
            f"_(Sinyal Buy/Sell resmi akan dikirim otomatis jika AI menemukan momentum yang tepat)_"
        )

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={
                "chat_id": channel_id,
                "text": message,
                "parse_mode": "Markdown"
            })
        print("[Daily Broadcast] Successfully sent daily anomalies to Telegram.")
    except Exception as e:
        print(f"[Daily Broadcast] Error: {e}")

def start_daily_broadcast_daemon():
    scheduler = AsyncIOScheduler()
    # Run every day at 16:30 WIB (09:30 UTC)
    scheduler.add_job(
        daily_telegram_broadcast,
        'cron',
        hour=9,
        minute=30,
        id="daily_telegram_broadcast",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    print("[Market Screener] Daily Broadcast Daemon started (scheduled for 16:30 WIB).")
