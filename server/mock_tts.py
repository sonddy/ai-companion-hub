"""
Lightweight mock TTS server for local/testing use when GPT-SoVITS isn't running.
Generates a short sine-wave WAV so the UI can receive and play audio without CORS issues.

Run from project root:
  uvicorn server.mock_tts:app --port 8002

You can then point the web page endpoint to http://127.0.0.1:8002/tts.
"""
import io
import math
import struct
import wave
from typing import Optional

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


class TTSRequest(BaseModel):
    text: str
    text_lang: str = "en"
    ref_audio_path: Optional[str] = None
    prompt_text: Optional[str] = None
    prompt_lang: str = "en"


def synthesize_tone(duration_sec: float = 2.0, sample_rate: int = 24000, freq_hz: float = 440.0) -> bytes:
    """Return a simple sine wave as WAV bytes."""
    frame_count = int(duration_sec * sample_rate)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(frame_count):
            value = int(32767 * math.sin(2 * math.pi * freq_hz * i / sample_rate))
            frames.extend(struct.pack("<h", value))
        wf.writeframes(frames)
    return buffer.getvalue()


app = FastAPI(title="Riko Mock TTS")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/tts")
def tts(_: TTSRequest):
    tone = synthesize_tone()
    return Response(content=tone, media_type="audio/wav")


@app.get("/health")
def health():
    return {"status": "ok", "mode": "mock"}







