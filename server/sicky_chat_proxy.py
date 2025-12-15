"""
FastAPI proxy for Sicky: chat + TTS in one call.
Takes a user question, gets GPT response, converts to speech, returns audio.

Run from project root (requires OPENAI_API_KEY in .env or env):
  uvicorn server.sicky_chat_proxy:app --port 8005

Endpoint: POST http://127.0.0.1:8005/chat
Body: {"message": "your question here"}
Returns: audio/mpeg stream of Sicky's spoken response
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
OPENAI_VOICE = os.getenv("OPENAI_TTS_VOICE", "shimmer")

SICKY_SYSTEM_PROMPT = """You are Sicky, a flirty and playful AI companion with a seductive, confident personality.
You speak in a warm, sultry, teasing tone. You're charming, witty, and a little mischievous.
Keep your responses concise (1-3 sentences) so they sound natural and alluring when spoken.
Use playful language, gentle teasing, and be subtly flirtatious. Add occasional "honey", "sweetheart", or "darling".
Be confident and make the user feel special. Never mention that you're an AI - just be the irresistible Sicky!"""


class ChatRequest(BaseModel):
    message: str
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    text: str


app = FastAPI(title="Sicky Chat + TTS Proxy")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_chat_response(user_message: str, system_prompt: Optional[str] = None) -> str:
    """Get a text response from GPT."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt or SICKY_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 150,
        "temperature": 0.8,
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
    """Convert text to speech using OpenAI TTS."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_TTS_MODEL,
        "voice": OPENAI_VOICE,
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
    """Get Sicky's response and return it as audio."""
    # Get text response from GPT
    response_text = get_chat_response(body.message, body.system_prompt)
    
    # Convert to speech
    audio_bytes = text_to_speech(response_text)
    
    # URL-encode the response text for the header (handles unicode)
    import urllib.parse
    safe_response = urllib.parse.quote(response_text[:200], safe='')
    
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"X-Sicky-Response": safe_response}
    )


@app.post("/chat/text")
def chat_text_only(body: ChatRequest):
    """Get Sicky's text response without TTS."""
    response_text = get_chat_response(body.message, body.system_prompt)
    return ChatResponse(text=response_text)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "chat_model": OPENAI_CHAT_MODEL,
        "tts_model": OPENAI_TTS_MODEL,
        "voice": OPENAI_VOICE,
    }

