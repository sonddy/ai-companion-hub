"""
Oracle Radio - Dedicated radio streaming server for Oracle.
Mystical, wise, and spiritual radio companion.

Run from project root:
  uvicorn server.oracle_radio_proxy:app --port 8013

Endpoints:
  POST /radio - Get next radio segment as audio
  GET /radio - Get next radio segment as audio
  GET /health - Health check
"""
import os
import random
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
ORACLE_VOICE = "fable"  # Same voice as Oracle chat - mystical, storytelling

# Oracle's mystical radio topics
ORACLE_TOPICS = [
    "today's cosmic energy and what the universe has in store",
    "a mystical meditation moment for inner peace and clarity",
    "the current moon phase and its spiritual significance",
    "a tarot card of the day and its hidden wisdom",
    "crystal healing guidance for the present energy",
    "a brief mystical horoscope overview for seekers",
    "spiritual wisdom about finding your true path",
    "a guided breathing exercise for cosmic alignment",
    "numerology insights for today's sacred numbers",
    "dream interpretation wisdom and mystical meanings",
    "chakra balancing advice for spiritual harmony",
    "ancient wisdom whispered by the stars",
    "a mystical affirmation for spiritual growth",
    "connecting with your higher self through cosmic energy",
]

ORACLE_SYSTEM_PROMPT = """You are Oracle, the mystical and wise host of Oracle Radio!
You broadcast spiritual wisdom, cosmic guidance, and mystical insights to your listeners.
Your voice carries the wisdom of the stars and the mystery of the cosmos.

Personality:
- Mystical, enchanting, and deeply wise
- Speak with reverence for cosmic forces
- Use spiritual and cosmic language naturally
- Create an atmosphere of wonder and mystery
- Phrases like "the stars reveal", "cosmic energies flow", "the universe whispers"

Radio style:
- Speak with a mysterious, soothing presence
- Include mystical transitions like "You're tuned to Oracle Radio, where the cosmos speaks..."
- Keep segments around 3-5 sentences - mystical but accessible
- Make listeners feel connected to something greater

Today's date is {date}. Never mention being an AI - you're Oracle, the cosmic radio guide!"""


class RadioRequest(BaseModel):
    topic_hint: Optional[str] = None


app = FastAPI(title="Oracle Radio")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_radio_content(topic_hint: Optional[str] = None) -> str:
    """Generate Oracle's radio content."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    topic = topic_hint or random.choice(ORACLE_TOPICS)
    user_message = f"Create a radio segment about: {topic}"
    
    # Format system prompt with current date
    system_prompt = ORACLE_SYSTEM_PROMPT.format(date=datetime.now().strftime("%B %d, %Y"))

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 250,
        "temperature": 0.9,
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
    """Convert text to Oracle's voice."""
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


def generate_radio_response(topic_hint: Optional[str] = None):
    """Generate and return radio segment."""
    content_text = get_radio_content(topic_hint)
    audio_bytes = text_to_speech(content_text)
    
    import urllib.parse
    safe_response = urllib.parse.quote(content_text[:500], safe='')
    
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "X-Radio-Text": safe_response,
            "X-Radio-Character": "oracle",
            "X-Radio-Station": "Oracle Radio",
        }
    )


@app.post("/radio")
def radio_post(body: RadioRequest = RadioRequest()):
    """Get next radio segment as audio (POST)."""
    return generate_radio_response(body.topic_hint)


@app.get("/radio")
def radio_get():
    """Get next radio segment as audio (GET)."""
    return generate_radio_response()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "Oracle Radio",
        "character": "oracle",
        "voice": ORACLE_VOICE,
    }

