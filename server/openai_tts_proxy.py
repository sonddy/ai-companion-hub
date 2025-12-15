"""
FastAPI proxy to call OpenAI text-to-speech and return audio to the browser.

Run from project root (requires OPENAI_API_KEY in env or .env file):
  uvicorn server.openai_tts_proxy:app --port 8003

Point the browser endpoint to: http://127.0.0.1:8003/tts
"""
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()  # loads .env from current directory

import requests
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_TTS_URL = "https://api.openai.com/v1/audio/speech"
OPENAI_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
OPENAI_VOICE = os.getenv("OPENAI_TTS_VOICE", "alloy")


class TTSRequest(BaseModel):
    text: str
    text_lang: Optional[str] = "en"
    ref_audio_path: Optional[str] = None
    prompt_text: Optional[str] = None
    prompt_lang: Optional[str] = "en"
    voice: Optional[str] = None
    model: Optional[str] = None


app = FastAPI(title="OpenAI TTS Proxy")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/tts")
def proxy_tts(body: TTSRequest):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    payload = {
        "model": body.model or OPENAI_MODEL,
        "voice": body.voice or OPENAI_VOICE,
        "input": body.text,
        "format": "mp3",
    }

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(
            OPENAI_TTS_URL, json=payload, headers=headers, timeout=60, stream=True
        )
        resp.raise_for_status()
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response else 502
        detail = exc.response.text if exc.response else str(exc)
        raise HTTPException(status_code=status, detail=detail)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return Response(content=resp.content, media_type="audio/mpeg")


@app.get("/health")
def health():
    return {"status": "ok", "model": OPENAI_MODEL, "voice": OPENAI_VOICE}

