"""
Simple FastAPI proxy for GPT-SoVITS that adds permissive CORS headers.
Use when calling the TTS endpoint from the browser to avoid CORS failures.

Run from project root:
  uvicorn server.tts_proxy:app --port 8001

Override the upstream TTS URL with the TARGET_TTS_URL environment variable.
"""
import os
from typing import Optional

import requests
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

TARGET_TTS_URL = os.getenv("TARGET_TTS_URL", "http://127.0.0.1:9880/tts")


class TTSRequest(BaseModel):
    text: str
    text_lang: str = "en"
    ref_audio_path: str
    prompt_text: str
    prompt_lang: str = "en"


app = FastAPI(title="Riko TTS Proxy")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/tts")
def proxy_tts(body: TTSRequest):
    try:
        forward = requests.post(TARGET_TTS_URL, json=body.dict(), timeout=60)
        forward.raise_for_status()
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response else 502
        detail = exc.response.text if exc.response else str(exc)
        raise HTTPException(status_code=status, detail=detail)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    media_type: Optional[str] = forward.headers.get("content-type", "audio/wav")
    return Response(content=forward.content, media_type=media_type)


@app.get("/health")
def health():
    return {"status": "ok", "target": TARGET_TTS_URL}












