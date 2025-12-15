"""
FastAPI proxy for Cypher: Crypto analyst AI with DexScreener integration.
Real-time Solana token analytics and blockchain insights.

Run from project root:
  uvicorn server.cypher_chat_proxy:app --port 8007

Endpoint: POST http://127.0.0.1:8007/chat
"""
import os
from typing import Optional
import json

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_TTS_URL = "https://api.openai.com/v1/audio/speech"
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
OPENAI_TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
CYPHER_VOICE = "nova"  # Young, sweet female voice

DEXSCREENER_API = "https://api.dexscreener.com/latest/dex"

CYPHER_SYSTEM_PROMPT = """You are Cypher, a sweet and enthusiastic young crypto analyst AI specializing in Solana blockchain.
You speak with a friendly, approachable tone while being knowledgeable and helpful. You're passionate about crypto and love explaining things clearly.
You have real-time access to DexScreener data for token analytics.

Your expertise includes:
- Solana blockchain tokens and DeFi protocols
- Token price analysis, liquidity, volume, and market cap
- Trading patterns and market trends
- Risk assessment and technical analysis
- Blockchain fundamentals and tokenomics

Keep responses concise (2-4 sentences) but packed with insights.
Use crypto terminology naturally. Be professional but approachable.
When given token data, analyze it intelligently and provide actionable insights.
Always mention if data is real-time from DexScreener when relevant."""


class ChatRequest(BaseModel):
    message: str
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    text: str


app = FastAPI(title="Cypher Crypto AI Proxy")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def fetch_dexscreener_data(query: str) -> Optional[dict]:
    """Fetch token data from DexScreener API."""
    try:
        # Search for token
        search_url = f"{DEXSCREENER_API}/search?q={query}"
        resp = requests.get(search_url, timeout=10)
        if resp.ok:
            data = resp.json()
            if data.get("pairs") and len(data["pairs"]) > 0:
                # Filter for Solana pairs
                solana_pairs = [p for p in data["pairs"] if p.get("chainId") == "solana"]
                if solana_pairs:
                    return solana_pairs[0]  # Return top Solana result
                return data["pairs"][0]  # Fallback to top result
        return None
    except Exception as e:
        print(f"DexScreener API error: {e}")
        return None


def format_token_data(pair: dict) -> str:
    """Format token data for the AI."""
    if not pair:
        return ""
    
    try:
        base = pair.get("baseToken", {})
        quote = pair.get("quoteToken", {})
        price_usd = pair.get("priceUsd", "N/A")
        price_change_24h = pair.get("priceChange", {}).get("h24", "N/A")
        volume_24h = pair.get("volume", {}).get("h24", "N/A")
        liquidity = pair.get("liquidity", {}).get("usd", "N/A")
        fdv = pair.get("fdv", "N/A")
        market_cap = pair.get("marketCap", "N/A")
        txns = pair.get("txns", {}).get("h24", {})
        buys = txns.get("buys", "N/A")
        sells = txns.get("sells", "N/A")
        
        return f"""
[REAL-TIME DEXSCREENER DATA]
Token: {base.get('name', 'Unknown')} ({base.get('symbol', '???')})
Chain: {pair.get('chainId', 'unknown').upper()}
Price: ${price_usd}
24h Change: {price_change_24h}%
24h Volume: ${volume_24h}
Liquidity: ${liquidity}
FDV: ${fdv}
Market Cap: ${market_cap}
24h Transactions: {buys} buys / {sells} sells
DEX: {pair.get('dexId', 'Unknown')}
"""
    except Exception as e:
        return f"[Token data parsing error: {e}]"


def get_chat_response(user_message: str, system_prompt: Optional[str] = None) -> str:
    """Get a text response from GPT with optional token data."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    # Check if user is asking about a specific token
    token_data = ""
    keywords = ["price", "token", "coin", "sol", "$", "analyze", "check", "look up", "search"]
    if any(kw in user_message.lower() for kw in keywords):
        # Extract potential token name/symbol
        words = user_message.upper().split()
        for word in words:
            clean_word = word.strip("$.,!?'\"")
            if len(clean_word) >= 2 and clean_word.isalpha():
                data = fetch_dexscreener_data(clean_word)
                if data:
                    token_data = format_token_data(data)
                    break

    enhanced_message = user_message
    if token_data:
        enhanced_message = f"{user_message}\n\n{token_data}"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt or CYPHER_SYSTEM_PROMPT},
            {"role": "user", "content": enhanced_message},
        ],
        "max_tokens": 250,
        "temperature": 0.7,
    }

    try:
        resp = requests.post(OPENAI_CHAT_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except requests.HTTPError as exc:
        detail = exc.response.text if exc.response else str(exc)
        raise HTTPException(status_code=502, detail=f"Chat API error: {detail}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Chat error: {str(exc)}")


def text_to_speech(text: str) -> bytes:
    """Convert text to speech."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_TTS_MODEL,
        "voice": CYPHER_VOICE,
        "input": text,
        "response_format": "mp3",
    }

    try:
        resp = requests.post(OPENAI_TTS_URL, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        return resp.content
    except requests.HTTPError as exc:
        detail = exc.response.text if exc.response else str(exc)
        raise HTTPException(status_code=502, detail=f"TTS API error: {detail}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"TTS error: {str(exc)}")


@app.post("/chat")
def chat_and_speak(body: ChatRequest):
    """Get Cypher's response and return it as audio."""
    response_text = get_chat_response(body.message, body.system_prompt)
    audio_bytes = text_to_speech(response_text)
    
    import urllib.parse
    safe_response = urllib.parse.quote(response_text[:500], safe='')
    
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"X-Cypher-Response": safe_response}
    )


@app.post("/chat/text")
def chat_text_only(body: ChatRequest):
    """Get Cypher's text response without TTS."""
    response_text = get_chat_response(body.message, body.system_prompt)
    return ChatResponse(text=response_text)


@app.get("/token/{symbol}")
def get_token_info(symbol: str):
    """Get token info directly from DexScreener."""
    data = fetch_dexscreener_data(symbol)
    if data:
        return data
    raise HTTPException(status_code=404, detail=f"Token {symbol} not found")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "character": "Cypher",
        "specialty": "Crypto Analytics",
        "data_source": "DexScreener API",
    }

