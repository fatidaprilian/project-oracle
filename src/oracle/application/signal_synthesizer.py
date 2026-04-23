import os
import json
import feedparser
from google import genai
from pydantic import BaseModel, Field

def fetch_news_for_ticker(ticker: str, max_headlines: int = 5) -> str:
    """
    Fetches the latest headlines for a given ticker from Yahoo Finance RSS.
    """
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    feed = feedparser.parse(url)
    
    if not feed.entries:
        return "No recent news found."
        
    headlines = []
    for entry in feed.entries[:max_headlines]:
        headlines.append(f"- {entry.title}")
        
    return "\n".join(headlines)

class OracleDecision(BaseModel):
    bias: str = Field(description="Must be 'BUY' or 'IGNORE'")
    reason: str = Field(description="Maksimal 2 kalimat alasan dalam bahasa Indonesia yang menjelaskan bias berdasarkan sinyal dan berita")

def synthesize_signal(ticker: str, signal_type: str, price: float, news: str) -> dict:
    """
    Uses Gemini API to synthesize the technical signal with fundamental news.
    Returns a dictionary with 'bias' and 'reason'.
    """
    api_key = os.getenv("ORACLE_AI_ANALYST_API_KEY")
    if not api_key:
        return {
            "bias": "IGNORE",
            "reason": "Kunci API Oracle AI Analyst belum tersedia. Sistem masuk ke mode aman."
        }
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
You are the Oracle Synthesizer, an expert financial analyst AI.
You need to decide whether a technical trading signal is valid based on recent fundamental news.

Ticker: {ticker}
Current Price: {price}
Technical Signal: {signal_type}

Recent Headlines:
{news}

If the news is strongly negative or contradicts a bullish technical signal, output 'IGNORE'.
If the news is positive or neutral and supports the technical signal, output 'BUY'.
Berikan alasan singkat dalam bahasa Indonesia profesional (maksimal 2 kalimat).
"""
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                'response_schema': OracleDecision,
                'temperature': 0.1,
            },
        )
        
        result = json.loads(response.text)
        return result
    except Exception as e:
        print(f"Gemini API error: {e}")
        return {
            "bias": "IGNORE",
            "reason": f"Sintesis AI gagal dilakukan: {str(e)}"
        }
