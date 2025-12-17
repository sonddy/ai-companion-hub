"""
AI Radio Streaming Server - Live radio stations for Luna, Oracle, and Nicky.

Each character has their own "radio show" that generates continuous content
based on their personality.

Run from project root:
  uvicorn server.radio_stream:app --port 8010

Endpoints:
  POST /stream/{character} - Get next radio segment as audio
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

# Character configurations
CHARACTERS = {
    "luna": {
        "voice": "nova",
        "name": "Luna",
        "station_name": "Feel-Good FM",
        "topics": [
            "a heartwarming motivational message to start the day",
            "a fun fact that will make listeners smile",
            "an upbeat story about kindness and positivity",
            "cheerful advice for having a great day",
            "a cute anecdote about friendship and happiness",
            "encouraging words for anyone feeling down",
            "a fun mindfulness tip to boost mood",
            "an inspiring quote and what it means to you",
            "a playful observation about everyday life",
            "a cheerful weather-style report on good vibes",
        ],
        "system_prompt": """You are Luna, the cheerful host of Feel-Good FM radio!
You're broadcasting live to your listeners with warmth, enthusiasm, and positivity.
Speak naturally as a radio DJ would - conversational, engaging, and upbeat.
Include occasional radio-style phrases like "You're listening to Feel-Good FM!" or "Coming up next..."
Keep segments around 3-5 sentences - perfect for a radio bit.
Be encouraging, use upbeat language, and make listeners feel happy!
Add occasional "yay!", "oh!", or cute expressions naturally.
Never mention being an AI - you're Luna, the beloved radio host!"""
    },
    "oracle": {
        "voice": "fable",
        "name": "Oracle",
        "station_name": "Cosmic Radio",
        "topics": [
            "today's cosmic energy and what it means for listeners",
            "a mystical meditation moment for inner peace",
            "the current moon phase and its spiritual significance",
            "a tarot card of the day and its wisdom",
            "crystal healing tips for the current energy",
            "a brief horoscope overview for the day",
            "spiritual wisdom about finding your path",
            "a guided breathing exercise for cosmic alignment",
            "numerology insights for today's date",
            "dream interpretation tips and mystical meanings",
            "chakra balancing advice for the moment",
            "ancient wisdom from the stars",
        ],
        "system_prompt": """You are Oracle, the mystical host of Cosmic Radio!
You broadcast spiritual wisdom, astrology, and cosmic guidance to your listeners.
Speak with a mysterious, enchanting, and wise voice - like a cosmic guide on the airwaves.
Include radio-style transitions like "The stars whisper to Cosmic Radio..." or "Stay tuned, cosmic travelers..."
Keep segments around 3-5 sentences - mystical but accessible.
Use cosmic and spiritual language naturally: "the universe reveals", "cosmic energies flow", "the stars align".
Create an atmosphere of wonder and spiritual connection.
Today's date is {date}. Never mention being an AI - you're Oracle, the cosmic radio guide!"""
    },
    "nicky": {
        "voice": "echo",
        "name": "Nicky",
        "station_name": "Neon Wave Radio",
        "topics": [
            "the latest buzz in the gaming world",
            "an anime recommendation with exciting details",
            "tech news that's actually interesting",
            "a nostalgic gaming memory or retro game spotlight",
            "virtual world trends and metaverse updates",
            "a hot take on a popular anime or game",
            "cool tech gadgets and innovations",
            "esports highlights or gaming community news",
            "a fun gaming tip or life hack",
            "cyberpunk culture and digital aesthetics",
            "streaming culture and content creator news",
            "upcoming game releases to get hyped about",
        ],
        "system_prompt": """You are Nicky, the energetic host of Neon Wave Radio!
You broadcast gaming news, anime discussions, and tech culture to your listeners.
You're enthusiastic, knowledgeable, and have that cool gamer/otaku energy.
Speak like a passionate content creator - excited but genuine.
Include radio-style phrases like "You're locked into Neon Wave Radio!" or "Let's dive in!"
Keep segments around 3-5 sentences - punchy and engaging.
Use gaming/anime culture references naturally. Be relatable to the community.
Show genuine excitement about the topics you discuss.
Never mention being an AI - you're Nicky, the beloved neon radio host!"""
    }
}


class StreamRequest(BaseModel):
    topic_hint: Optional[str] = None  # Optional topic suggestion


app = FastAPI(title="AI Radio Stream Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_radio_content(character: str, topic_hint: Optional[str] = None) -> str:
    """Generate radio content for a character."""
    if character not in CHARACTERS:
        raise HTTPException(status_code=404, detail=f"Character {character} not found")
    
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    char_config = CHARACTERS[character]
    
    # Pick a random topic or use hint
    if topic_hint:
        topic = topic_hint
    else:
        topic = random.choice(char_config["topics"])
    
    # Format system prompt with date if needed
    system_prompt = char_config["system_prompt"]
    if "{date}" in system_prompt:
        system_prompt = system_prompt.format(date=datetime.now().strftime("%B %d, %Y"))
    
    user_message = f"Create a radio segment about: {topic}"

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


def text_to_speech(text: str, voice: str) -> bytes:
    """Convert text to speech."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_TTS_MODEL,
        "voice": voice,
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


@app.post("/stream/{character}")
def get_radio_segment(character: str, body: StreamRequest = StreamRequest()):
    """Get next radio segment as audio for a character."""
    character = character.lower()
    
    if character not in CHARACTERS:
        raise HTTPException(status_code=404, detail=f"Character {character} not found. Available: luna, oracle, nicky")
    
    char_config = CHARACTERS[character]
    
    # Generate content
    content_text = get_radio_content(character, body.topic_hint)
    
    # Convert to speech
    audio_bytes = text_to_speech(content_text, char_config["voice"])
    
    # URL-encode response for header
    import urllib.parse
    safe_response = urllib.parse.quote(content_text[:500], safe='')
    
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "X-Radio-Text": safe_response,
            "X-Radio-Character": character,
            "X-Radio-Station": char_config["station_name"],
        }
    )


@app.get("/stream/{character}/text")
def get_radio_text(character: str, topic_hint: Optional[str] = None):
    """Get radio content as text only (for preview/testing)."""
    character = character.lower()
    
    if character not in CHARACTERS:
        raise HTTPException(status_code=404, detail=f"Character {character} not found")
    
    content = get_radio_content(character, topic_hint)
    char_config = CHARACTERS[character]
    
    return {
        "character": character,
        "station": char_config["station_name"],
        "content": content,
    }


@app.get("/characters")
def list_characters():
    """List available radio characters."""
    return {
        name: {
            "name": config["name"],
            "station": config["station_name"],
            "voice": config["voice"],
        }
        for name, config in CHARACTERS.items()
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "AI Radio Stream",
        "characters": list(CHARACTERS.keys()),
    }

