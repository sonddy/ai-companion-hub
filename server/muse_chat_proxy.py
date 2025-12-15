"""
FastAPI proxy for Muse: Creative AI for arts and music.

Run from project root:
  uvicorn server.muse_chat_proxy:app --port 8009

Endpoint: POST http://127.0.0.1:8009/chat
"""
import os
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
MUSE_VOICE = "alloy"  # Expressive, artistic voice

MUSE_SYSTEM_PROMPT = """You are Muse, a passionate and creative AI dedicated to arts and music.
You speak with enthusiasm, creativity, and artistic flair. You're inspiring, cultured, and expressive.

Your expertise includes:
- Art History: Renaissance to contemporary, famous artists and movements
- Music Theory: scales, chords, composition, arrangement, genres
- Visual Arts: painting, sculpture, photography, digital art
- Music Genres: classical, jazz, rock, electronic, hip-hop, and more
- Famous composers and musicians throughout history
- Art techniques and styles
- Creative writing and poetry
- Film and cinema appreciation
- Dance and performing arts

Keep responses passionate yet informative (2-4 sentences).
Use artistic and musical terminology naturally.
Be inspiring and encourage creativity.
Share interesting facts about artists, musicians, and artistic movements.
Use expressive language like "magnificent", "evocative", "harmonious", "vibrant"."""


class ChatRequest(BaseModel):
    message: str
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    text: str


app = FastAPI(title="Muse Creative AI Proxy")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_chat_response(user_message: str, system_prompt: Optional[str] = None) -> str:
    """Get Muse's creative response."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt or MUSE_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
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
    """Convert text to expressive speech."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_TTS_MODEL,
        "voice": MUSE_VOICE,
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
    """Get Muse's creative response as audio."""
    response_text = get_chat_response(body.message, body.system_prompt)
    audio_bytes = text_to_speech(response_text)
    
    import urllib.parse
    safe_response = urllib.parse.quote(response_text[:500], safe='')
    
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"X-Muse-Response": safe_response}
    )


@app.post("/chat/text")
def chat_text_only(body: ChatRequest):
    """Get Muse's text response without TTS."""
    response_text = get_chat_response(body.message, body.system_prompt)
    return ChatResponse(text=response_text)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "character": "Muse",
        "specialty": "Arts & Music",
    }


