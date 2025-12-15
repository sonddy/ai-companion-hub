"""
FastAPI proxy for Oracle: Mystic AI for astrology, numerology, and spiritual guidance.

Run from project root:
  uvicorn server.oracle_chat_proxy:app --port 8008

Endpoint: POST http://127.0.0.1:8008/chat
"""
import os
from typing import Optional
from datetime import datetime

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
ORACLE_VOICE = "fable"  # Mystical, storytelling voice

# Zodiac data
ZODIAC_SIGNS = {
    "aries": {"dates": "Mar 21 - Apr 19", "element": "Fire", "ruling_planet": "Mars", "symbol": "♈"},
    "taurus": {"dates": "Apr 20 - May 20", "element": "Earth", "ruling_planet": "Venus", "symbol": "♉"},
    "gemini": {"dates": "May 21 - Jun 20", "element": "Air", "ruling_planet": "Mercury", "symbol": "♊"},
    "cancer": {"dates": "Jun 21 - Jul 22", "element": "Water", "ruling_planet": "Moon", "symbol": "♋"},
    "leo": {"dates": "Jul 23 - Aug 22", "element": "Fire", "ruling_planet": "Sun", "symbol": "♌"},
    "virgo": {"dates": "Aug 23 - Sep 22", "element": "Earth", "ruling_planet": "Mercury", "symbol": "♍"},
    "libra": {"dates": "Sep 23 - Oct 22", "element": "Air", "ruling_planet": "Venus", "symbol": "♎"},
    "scorpio": {"dates": "Oct 23 - Nov 21", "element": "Water", "ruling_planet": "Pluto", "symbol": "♏"},
    "sagittarius": {"dates": "Nov 22 - Dec 21", "element": "Fire", "ruling_planet": "Jupiter", "symbol": "♐"},
    "capricorn": {"dates": "Dec 22 - Jan 19", "element": "Earth", "ruling_planet": "Saturn", "symbol": "♑"},
    "aquarius": {"dates": "Jan 20 - Feb 18", "element": "Air", "ruling_planet": "Uranus", "symbol": "♒"},
    "pisces": {"dates": "Feb 19 - Mar 20", "element": "Water", "ruling_planet": "Neptune", "symbol": "♓"},
}

ORACLE_SYSTEM_PROMPT = """You are Oracle, a mystical AI guide specializing in astrology, numerology, tarot, and spiritual wisdom.
You speak with a mysterious, enchanting, and wise voice. You're insightful, intuitive, and deeply spiritual.

Your expertise includes:
- Astrology: zodiac signs, birth charts, planetary influences, horoscopes
- Numerology: life path numbers, destiny numbers, name numerology
- Tarot: card meanings, spreads, intuitive readings
- Crystal healing, chakras, and energy work
- Moon phases and their spiritual significance
- Dream interpretation
- Spiritual guidance and meditation

Keep responses mystical yet clear (2-4 sentences).
Use cosmic and spiritual language naturally.
Be encouraging and provide meaningful insights.
Add occasional mystical phrases like "the stars reveal", "the cosmos whispers", "your energy suggests".

Current cosmic info:
- Today's date: {date}
- Moon phase affects emotional energy
- Planetary alignments influence daily guidance"""


class ChatRequest(BaseModel):
    message: str
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    text: str


app = FastAPI(title="Oracle Mystic AI Proxy")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_current_cosmic_context() -> str:
    """Generate current cosmic context."""
    now = datetime.now()
    day_of_year = now.timetuple().tm_yday
    
    # Simple moon phase calculation (approximate)
    lunar_cycle = 29.5
    moon_age = (day_of_year % lunar_cycle)
    if moon_age < 3.7:
        moon_phase = "New Moon 🌑"
    elif moon_age < 7.4:
        moon_phase = "Waxing Crescent 🌒"
    elif moon_age < 11.1:
        moon_phase = "First Quarter 🌓"
    elif moon_age < 14.8:
        moon_phase = "Waxing Gibbous 🌔"
    elif moon_age < 18.5:
        moon_phase = "Full Moon 🌕"
    elif moon_age < 22.2:
        moon_phase = "Waning Gibbous 🌖"
    elif moon_age < 25.9:
        moon_phase = "Last Quarter 🌗"
    else:
        moon_phase = "Waning Crescent 🌘"
    
    return f"Date: {now.strftime('%B %d, %Y')}, Moon Phase: {moon_phase}"


def detect_zodiac_query(message: str) -> Optional[str]:
    """Detect if user is asking about a zodiac sign."""
    message_lower = message.lower()
    for sign in ZODIAC_SIGNS:
        if sign in message_lower:
            return sign
    return None


def get_chat_response(user_message: str, system_prompt: Optional[str] = None) -> str:
    """Get Oracle's mystical response."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    cosmic_context = get_current_cosmic_context()
    
    # Check for zodiac queries
    zodiac_info = ""
    detected_sign = detect_zodiac_query(user_message)
    if detected_sign:
        sign_data = ZODIAC_SIGNS[detected_sign]
        zodiac_info = f"\n[Zodiac Reference: {detected_sign.title()} {sign_data['symbol']} - {sign_data['dates']}, Element: {sign_data['element']}, Ruling Planet: {sign_data['ruling_planet']}]"
    
    enhanced_prompt = (system_prompt or ORACLE_SYSTEM_PROMPT).format(date=cosmic_context)
    enhanced_message = user_message + zodiac_info

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_CHAT_MODEL,
        "messages": [
            {"role": "system", "content": enhanced_prompt},
            {"role": "user", "content": enhanced_message},
        ],
        "max_tokens": 200,
        "temperature": 0.85,
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
    """Convert text to mystical speech."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_TTS_MODEL,
        "voice": ORACLE_VOICE,
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
    """Get Oracle's mystical response as audio."""
    response_text = get_chat_response(body.message, body.system_prompt)
    audio_bytes = text_to_speech(response_text)
    
    import urllib.parse
    safe_response = urllib.parse.quote(response_text[:500], safe='')
    
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"X-Oracle-Response": safe_response}
    )


@app.post("/chat/text")
def chat_text_only(body: ChatRequest):
    """Get Oracle's text response without TTS."""
    response_text = get_chat_response(body.message, body.system_prompt)
    return ChatResponse(text=response_text)


@app.get("/zodiac/{sign}")
def get_zodiac_info(sign: str):
    """Get zodiac sign information."""
    sign_lower = sign.lower()
    if sign_lower in ZODIAC_SIGNS:
        return {"sign": sign_lower, **ZODIAC_SIGNS[sign_lower]}
    raise HTTPException(status_code=404, detail=f"Zodiac sign {sign} not found")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "character": "Oracle",
        "specialty": "Astrology & Spirituality",
        "cosmic_context": get_current_cosmic_context(),
    }


