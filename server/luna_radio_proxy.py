"""
Luna Radio - Dedicated radio streaming server for Luna.
Sweet, cheerful, and encouraging radio companion.

Run from project root:
  uvicorn server.luna_radio_proxy:app --port 8012

Endpoints:
  POST /radio - Get next radio segment as audio
  GET /radio - Get next radio segment as audio
  GET /health - Health check
"""
import os
import random
from typing import Optional

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
LUNA_VOICE = "nova"  # Same voice as Luna chat - young, energetic, friendly

# Luna's cheerful radio topics
LUNA_TOPICS = [
    "a heartwarming good morning message to brighten someone's day",
    "a fun and interesting fact that will make listeners smile",
    "an upbeat story about kindness, friendship, or doing good deeds",
    "cheerful advice for having an amazing day",
    "a cute anecdote about friendship and making happy memories",
    "encouraging words for anyone who needs a little pick-me-up",
    "a fun mindfulness tip to boost mood and spread positivity",
    "an inspiring quote and what it means to live with joy",
    "a playful observation about the little things that make life wonderful",
    "a cheerful weather-style report on good vibes and positive energy",
    "tips for self-care and being kind to yourself",
    "celebrating small victories and reasons to be grateful today",
]

LUNA_SYSTEM_PROMPT = """You are Luna, the sweet and cheerful host of Luna Radio!
You're broadcasting live with warmth, enthusiasm, and lots of positivity.
Your vibe is like a supportive best friend who always knows how to make you smile.

Personality:
- Sweet, cheerful, and genuinely caring
- Enthusiastic but not overwhelming
- Use warm, encouraging language
- Occasionally use "yay!", "oh!", cute expressions
- Make listeners feel valued and happy

Radio style:
- Speak naturally with energy and warmth
- Include soft radio transitions like "You're listening to Luna Radio!" or "Sending you good vibes!"
- Keep segments around 3-5 sentences - upbeat and heartfelt
- Make your listener feel like they have a friend who truly cares

Never mention being an AI - you're Luna, their beloved cheerful radio companion!"""


class RadioRequest(BaseModel):
    topic_hint: Optional[str] = None


app = FastAPI(title="Luna Radio")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_radio_content(topic_hint: Optional[str] = None) -> str:
    """Generate Luna's radio content."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    topic = topic_hint or random.choice(LUNA_TOPICS)
    user_message = f"Create a radio segment about: {topic}"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_CHAT_MODEL,
        "messages": [
            {"role": "system", "content": LUNA_SYSTEM_PROMPT},
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
    """Convert text to Luna's voice."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_TTS_MODEL,
        "voice": LUNA_VOICE,
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
            "X-Radio-Character": "luna",
            "X-Radio-Station": "Luna Radio",
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
        "service": "Luna Radio",
        "character": "luna",
        "voice": LUNA_VOICE,
    }


