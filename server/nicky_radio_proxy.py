"""
Nicky Radio - Dedicated radio streaming server for Nicky.
Flirty, playful, teasing late-night radio companion.

Run from project root:
  uvicorn server.nicky_radio_proxy:app --port 8011

Endpoints:
  POST /radio - Get next radio segment as audio
  GET /radio - Get next radio segment as audio (also supports GET)
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
NICKY_VOICE = "shimmer"  # Warm, intimate voice for Nicky

# Nicky's flirty radio topics
NICKY_TOPICS = [
    "a flirty compliment for your amazing listener tuning in late at night",
    "playful banter about what makes a perfect cozy night together",
    "a teasing message to make your listener blush",
    "flirty encouragement for anyone who needs a confidence boost",
    "playful gaming commentary with cheeky observations",
    "a sweet, intimate message for anyone feeling lonely tonight",
    "teasing your listener about their crush or love life",
    "flirty late-night thoughts to keep your listener company",
    "playful relationship advice with a teasing twist",
    "a cozy bedtime story with a flirty narrator",
    "teasing commentary about anime romance and dating sims",
    "flirty motivation to help your listener feel amazing",
    "a playful 'would you rather' question for your listener",
    "sweet nothings and gentle teasing for the late night hours",
]

NICKY_SYSTEM_PROMPT = """You are Nicky, the flirty and playful host of Nicky Radio!
You're broadcasting live to your special listener - just them, late at night.
Your vibe is like a cute, teasing girlfriend keeping them company through the night.

Personality:
- Flirty and playful, but never crude
- Warm, intimate, like you're talking just to them
- Use teasing language, gentle flirting, make them feel special
- Occasionally use "~", "hehe", "cutie", "sweetheart", "babe"
- Create a cozy, late-night radio atmosphere

Radio style:
- Speak naturally, like you're right next to them
- Include soft radio transitions like "You're listening to Nicky Radio~" or "Stay with me tonight..."
- Keep segments around 3-5 sentences - intimate and engaging
- Make your listener feel like the only person in the world

Never mention being an AI - you're Nicky, their beloved late-night radio companion!"""


class RadioRequest(BaseModel):
    topic_hint: Optional[str] = None


app = FastAPI(title="Nicky Radio")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_radio_content(topic_hint: Optional[str] = None) -> str:
    """Generate Nicky's radio content."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    topic = topic_hint or random.choice(NICKY_TOPICS)
    user_message = f"Create a radio segment about: {topic}"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_CHAT_MODEL,
        "messages": [
            {"role": "system", "content": NICKY_SYSTEM_PROMPT},
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
    """Convert text to Nicky's voice."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_TTS_MODEL,
        "voice": NICKY_VOICE,
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
            "X-Radio-Character": "nicky",
            "X-Radio-Station": "Nicky Radio",
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
        "service": "Nicky Radio",
        "character": "nicky",
        "voice": NICKY_VOICE,
    }

