import httpx
import asyncio
from datetime import datetime, timezone
import os

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
        
        anomalies = []
        for item in data.get("data", []):
            d = item.get("d", [])
            if len(d) >= 5:
                ticker = d[0]  # format: 'IDX:WBSA' or 'WBSA'
                close_price = d[1]
                volume = d[2]
                avg_vol_10d = d[3]
                change_pct = d[4]
                
                # Check for Volume Anomaly (Volume > 2.5x of 10-day average)
                # and ensure it's not a penny stock with tiny volume
                if avg_vol_10d > 100000 and volume > (avg_vol_10d * 2.5):
                    # Format for yfinance
                    yf_ticker = f"{ticker}.JK"
                    anomalies.append(yf_ticker)
                    
        print(f"[Market Screener] Found {len(anomalies)} volume anomalies.")
        return anomalies
    except Exception as e:
        print(f"[Market Screener] Error fetching screener data: {e}")
        return []

def run_market_screener():
    print("[Market Screener] Scanning IDX for volume anomalies...")
    anomalies = fetch_anomalous_stocks()
    
    if not anomalies:
        return
        
    try:
        from oracle.infrastructure.postgres_repository import add_to_watchlist
        added_count = 0
        for ticker in anomalies:
            # We add them to the watchlist. The auto_signal_generator will pick them up
            # on its next run and do the deep analysis.
            add_to_watchlist(ticker)
            added_count += 1
            
        print(f"[Market Screener] Successfully added {added_count} new anomalies to watchlist.")
    except Exception as e:
        print(f"[Market Screener] Failed to add to DB watchlist: {e}")
