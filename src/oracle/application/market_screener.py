import httpx
import asyncio
from datetime import datetime, timezone, timedelta
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from oracle.application.anomaly_policy import classify_volume_anomaly
from oracle.application.message_formats import format_daily_broadcast_message


def _screener_result_limit() -> int:
    raw_limit = os.getenv("ORACLE_MARKET_SCREENER_LIMIT", "12")
    try:
        parsed_limit = int(raw_limit)
    except (TypeError, ValueError):
        parsed_limit = 12
    return max(5, min(parsed_limit, 30))


def fetch_anomalous_stock_candidates() -> list[dict]:
    """
    Fetch Indonesian stocks from TradingView screener that have unusual volume.
    Returns anomaly candidates with discovery lane metadata.
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
        
        anomaly_candidates = []
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
                    lane_decision = classify_volume_anomaly(
                        close_price=float(close_price),
                        volume_ratio=float(ratio),
                        change_pct=float(change_pct),
                    )
                    anomaly_candidates.append({
                        "ticker": yf_ticker,
                        "lane": lane_decision.lane,
                        "reason": lane_decision.reason,
                        "discovery_score": lane_decision.discovery_score,
                        "volume_ratio": round(float(ratio), 2),
                        "change_pct": round(float(change_pct), 2),
                        "close_price": float(close_price),
                        "source": "TRADINGVIEW_VOLUME_SCREENER",
                    })
                    
        # Sort by the discovery score first, then the highest volume spike ratio.
        anomaly_candidates.sort(
            key=lambda candidate: (
                candidate["discovery_score"],
                candidate["volume_ratio"],
            ),
            reverse=True,
        )
        
        anomalies = anomaly_candidates[:_screener_result_limit()]
        
        print(f"[Market Screener] Found {len(anomalies)} top anomalies.")
        return anomalies
    except Exception as e:
        print(f"[Market Screener] Error fetching screener data: {e}")
        return []


def fetch_anomalous_stocks() -> list[str]:
    return [
        candidate["ticker"]
        for candidate in fetch_anomalous_stock_candidates()
    ]


def run_market_screener() -> list[str]:
    print("[Market Screener] Scanning IDX for volume anomalies...")
    anomaly_candidates = fetch_anomalous_stock_candidates()
    anomalies = [candidate["ticker"] for candidate in anomaly_candidates]
    
    if not anomalies:
        return []
        
    try:
        from oracle.infrastructure.postgres_repository import save_daily_anomalies
        save_daily_anomalies(anomaly_candidates)
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

        now_wib = datetime.now(timezone.utc) + timedelta(hours=7)
        message = format_daily_broadcast_message(anomalies, now_wib)

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
