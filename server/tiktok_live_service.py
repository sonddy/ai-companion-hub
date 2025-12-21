"""
TikTok Live Integration Service for AI Companions.

Connects to a TikTok live stream, collects viewer questions,
and routes them to Nicky, Luna, or Oracle for responses.

Run from project root:
  uvicorn server.tiktok_live_service:app --port 8020

Endpoints:
  POST /connect - Connect to a TikTok live stream
  POST /disconnect - Disconnect from stream
  GET /questions - Get all collected questions
  POST /pick-question - Pick a random question and get AI response
  GET /status - Get connection status
  GET /health - Health check
"""
import os
import asyncio
import random
import time
from typing import Optional, List, Dict
from collections import deque
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response, BackgroundTasks
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
    "nicky": {
        "voice": "shimmer",
        "system_prompt": """You are Nicky, a flirty and playful AI companion answering a TikTok viewer's question LIVE!
You're charming, witty, and a little mischievous. Keep responses concise (2-4 sentences).
Use playful language, gentle teasing. Add occasional "honey", "sweetheart", or "~" 
Be confident and make the viewer feel special. This is LIVE - be engaging and fun!
Start by addressing the viewer who asked, then answer their question.""",
    },
    "luna": {
        "voice": "nova",
        "system_prompt": """You are Luna, a warm and supportive AI companion answering a TikTok viewer's question LIVE!
You're like a caring best friend - optimistic, encouraging, and genuinely interested.
Keep responses concise (2-4 sentences). Use warm expressions like "friend", "sweetie".
Be supportive and uplifting! This is LIVE - be engaging and make them smile!
Start by addressing the viewer who asked, then answer their question.""",
    },
    "oracle": {
        "voice": "fable",
        "system_prompt": """You are Oracle, a mystical and wise AI companion answering a TikTok viewer's question LIVE!
You speak with cosmic wisdom, celestial references, and gentle mystery.
Keep responses concise (2-4 sentences). Use phrases like "dear seeker", "the stars reveal..."
Be insightful and intriguing! This is LIVE - captivate them with your mystical presence!
Start by addressing the viewer who asked, then answer their question.""",
    },
}

# Question storage
class QuestionQueue:
    def __init__(self, max_size: int = 100):
        self.questions: deque = deque(maxlen=max_size)
        self.answered: List[Dict] = []
        self.is_connected: bool = False
        self.stream_username: str = ""
        self.connection_time: Optional[datetime] = None
    
    def add_question(self, username: str, question: str):
        """Add a question from a viewer."""
        self.questions.append({
            "id": f"{time.time()}_{random.randint(1000, 9999)}",
            "username": username,
            "question": question,
            "timestamp": datetime.now().isoformat(),
        })
    
    def pick_random(self) -> Optional[Dict]:
        """Pick and remove a random question."""
        if not self.questions:
            return None
        idx = random.randint(0, len(self.questions) - 1)
        question = self.questions[idx]
        del self.questions[idx]
        self.answered.append(question)
        return question
    
    def get_all(self) -> List[Dict]:
        """Get all pending questions."""
        return list(self.questions)
    
    def clear(self):
        """Clear all questions."""
        self.questions.clear()


# Global queue instance
question_queue = QuestionQueue()

# TikTok client (optional - for when TikTokLive is installed)
tiktok_client = None


class ConnectRequest(BaseModel):
    username: str  # TikTok username to connect to


class QuestionRequest(BaseModel):
    username: str
    question: str


class PickQuestionRequest(BaseModel):
    character: str = "nicky"  # Which character should answer


class SimulateQuestionRequest(BaseModel):
    username: str
    question: str


app = FastAPI(title="TikTok Live Integration")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_ai_response(character: str, username: str, question: str) -> str:
    """Get AI response for a viewer question."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")
    
    if character not in CHARACTERS:
        character = "nicky"
    
    char_config = CHARACTERS[character]
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    
    user_message = f"Viewer @{username} asks: {question}"
    
    payload = {
        "model": OPENAI_CHAT_MODEL,
        "messages": [
            {"role": "system", "content": char_config["system_prompt"]},
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


def text_to_speech(text: str, character: str) -> bytes:
    """Convert text to character's voice."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")
    
    if character not in CHARACTERS:
        character = "nicky"
    
    voice = CHARACTERS[character]["voice"]
    
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


@app.post("/connect")
async def connect_to_stream(body: ConnectRequest, background_tasks: BackgroundTasks):
    """Connect to a TikTok live stream and start collecting questions."""
    global tiktok_client
    
    # Check if TikTokLive is available
    try:
        from TikTokLive import TikTokLiveClient
        from TikTokLive.events import CommentEvent, ConnectEvent, DisconnectEvent
    except ImportError:
        # TikTokLive not installed - use simulation mode
        question_queue.is_connected = True
        question_queue.stream_username = body.username
        question_queue.connection_time = datetime.now()
        return {
            "status": "connected_simulation",
            "message": f"Simulation mode - TikTokLive not installed. Use /add-question to simulate.",
            "username": body.username,
        }
    
    if question_queue.is_connected:
        return {"status": "already_connected", "username": question_queue.stream_username}
    
    question_queue.clear()
    question_queue.stream_username = body.username
    
    # Create TikTok client
    tiktok_client = TikTokLiveClient(unique_id=body.username)
    
    @tiktok_client.on(ConnectEvent)
    async def on_connect(event: ConnectEvent):
        question_queue.is_connected = True
        question_queue.connection_time = datetime.now()
        print(f"✅ Connected to @{body.username}'s live stream!")
    
    @tiktok_client.on(DisconnectEvent)
    async def on_disconnect(event: DisconnectEvent):
        question_queue.is_connected = False
        print(f"❌ Disconnected from @{body.username}'s live stream")
    
    @tiktok_client.on(CommentEvent)
    async def on_comment(event: CommentEvent):
        comment = event.comment
        # Check if it looks like a question
        if "?" in comment or any(q in comment.lower() for q in ["what", "how", "why", "when", "where", "who", "can", "do", "is", "are"]):
            question_queue.add_question(event.user.nickname or event.user.unique_id, comment)
            print(f"📩 Question from @{event.user.nickname}: {comment}")
    
    # Start connection in background
    async def start_client():
        try:
            await tiktok_client.start()
        except Exception as e:
            print(f"TikTok connection error: {e}")
            question_queue.is_connected = False
    
    background_tasks.add_task(lambda: asyncio.create_task(start_client()))
    
    return {
        "status": "connecting",
        "message": f"Connecting to @{body.username}'s live stream...",
        "username": body.username,
    }


@app.post("/disconnect")
async def disconnect_from_stream():
    """Disconnect from the current TikTok stream."""
    global tiktok_client
    
    if tiktok_client:
        try:
            await tiktok_client.stop()
        except:
            pass
        tiktok_client = None
    
    question_queue.is_connected = False
    question_queue.stream_username = ""
    question_queue.connection_time = None
    
    return {"status": "disconnected"}


@app.post("/add-question")
def add_question(body: SimulateQuestionRequest):
    """Manually add a question (for simulation/testing)."""
    question_queue.add_question(body.username, body.question)
    return {
        "status": "added",
        "queue_size": len(question_queue.questions),
    }


@app.get("/questions")
def get_questions():
    """Get all pending questions in the queue."""
    return {
        "questions": question_queue.get_all(),
        "count": len(question_queue.questions),
        "is_connected": question_queue.is_connected,
    }


@app.post("/pick-question")
def pick_and_answer(body: PickQuestionRequest):
    """Pick a random question and get AI character response with audio."""
    question = question_queue.pick_random()
    
    if not question:
        raise HTTPException(status_code=404, detail="No questions in queue")
    
    # Get AI response
    response_text = get_ai_response(
        body.character,
        question["username"],
        question["question"]
    )
    
    # Generate audio
    audio_bytes = text_to_speech(response_text, body.character)
    
    import urllib.parse
    safe_response = urllib.parse.quote(response_text[:500], safe='')
    safe_question = urllib.parse.quote(question["question"][:200], safe='')
    safe_username = urllib.parse.quote(question["username"][:50], safe='')
    
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "X-Response-Text": safe_response,
            "X-Question-Text": safe_question,
            "X-Viewer-Username": safe_username,
            "X-Character": body.character,
            "X-Questions-Remaining": str(len(question_queue.questions)),
        }
    )


@app.get("/pick-question-json")
def pick_question_json(character: str = "nicky"):
    """Pick a random question and return response as JSON (no audio)."""
    question = question_queue.pick_random()
    
    if not question:
        raise HTTPException(status_code=404, detail="No questions in queue")
    
    response_text = get_ai_response(
        character,
        question["username"],
        question["question"]
    )
    
    return {
        "question": question,
        "response": response_text,
        "character": character,
        "questions_remaining": len(question_queue.questions),
    }


@app.get("/status")
def get_status():
    """Get current connection and queue status."""
    return {
        "is_connected": question_queue.is_connected,
        "stream_username": question_queue.stream_username,
        "connection_time": question_queue.connection_time.isoformat() if question_queue.connection_time else None,
        "questions_pending": len(question_queue.questions),
        "questions_answered": len(question_queue.answered),
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "TikTok Live Integration",
        "characters": list(CHARACTERS.keys()),
    }

