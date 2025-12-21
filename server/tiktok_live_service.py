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
import threading
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
        self.error_message: str = ""
        self.tiktok_available: bool = False
        self._lock = threading.Lock()
    
    def add_question(self, username: str, question: str):
        """Add a question from a viewer."""
        with self._lock:
            self.questions.append({
                "id": f"{time.time()}_{random.randint(1000, 9999)}",
                "username": username,
                "question": question,
                "timestamp": datetime.now().isoformat(),
            })
            print(f"[QUESTION] Added from @{username}: {question}")
    
    def pick_random(self) -> Optional[Dict]:
        """Pick and remove a random question."""
        with self._lock:
            if not self.questions:
                return None
            idx = random.randint(0, len(self.questions) - 1)
            question = self.questions[idx]
            del self.questions[idx]
            self.answered.append(question)
            return question
    
    def get_all(self) -> List[Dict]:
        """Get all pending questions."""
        with self._lock:
            return list(self.questions)
    
    def clear(self):
        """Clear all questions."""
        with self._lock:
            self.questions.clear()


# Global queue instance
question_queue = QuestionQueue()

# TikTok client reference
tiktok_client = None
tiktok_thread = None


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


def run_tiktok_client_in_thread(username: str):
    """Run the TikTok client in a separate thread with its own event loop."""
    global tiktok_client
    
    try:
        from TikTokLive import TikTokLiveClient
        from TikTokLive.events import ConnectEvent, DisconnectEvent, CommentEvent
        
        question_queue.tiktok_available = True
        
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Create TikTok client
        client = TikTokLiveClient(unique_id=username)
        tiktok_client = client
        
        @client.on(ConnectEvent)
        async def on_connect(event: ConnectEvent):
            question_queue.is_connected = True
            question_queue.connection_time = datetime.now()
            question_queue.error_message = ""
            print(f"[CONNECTED] Connected to @{username}'s TikTok live stream!")
        
        @client.on(DisconnectEvent)
        async def on_disconnect(event: DisconnectEvent):
            question_queue.is_connected = False
            print(f"[DISCONNECTED] Disconnected from @{username}'s TikTok live stream")
        
        @client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            comment = event.comment
            viewer_name = event.user.nickname or event.user.unique_id or "Anonymous"
            
            # Check if it looks like a question or is interesting
            is_question = (
                "?" in comment or 
                any(q in comment.lower() for q in [
                    "what", "how", "why", "when", "where", "who", 
                    "can", "do", "is", "are", "will", "would", "should",
                    "tell me", "explain", "help", "advice"
                ])
            )
            
            if is_question:
                question_queue.add_question(viewer_name, comment)
        
        # Run the client
        print(f"[CONNECTING] Attempting to connect to @{username}'s TikTok live...")
        loop.run_until_complete(client.start())
        
    except ImportError as e:
        question_queue.tiktok_available = False
        question_queue.error_message = "TikTokLive library not installed. Install with: pip install TikTokLive"
        print(f"[ERROR] TikTokLive not installed: {e}")
    except Exception as e:
        question_queue.is_connected = False
        question_queue.error_message = str(e)
        print(f"[ERROR] TikTok connection error: {e}")


@app.post("/connect")
def connect_to_stream(body: ConnectRequest):
    """Connect to a TikTok live stream and start collecting questions."""
    global tiktok_client, tiktok_thread
    
    username = body.username.replace("@", "").strip()
    
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    
    # Check if already connected
    if question_queue.is_connected:
        return {
            "status": "already_connected", 
            "username": question_queue.stream_username,
            "message": f"Already connected to @{question_queue.stream_username}"
        }
    
    # Clear previous state
    question_queue.clear()
    question_queue.stream_username = username
    question_queue.error_message = ""
    
    # Try to import TikTokLive to check availability
    try:
        from TikTokLive import TikTokLiveClient
        question_queue.tiktok_available = True
    except ImportError:
        question_queue.tiktok_available = False
        question_queue.is_connected = True  # Simulation mode
        question_queue.connection_time = datetime.now()
        return {
            "status": "simulation_mode",
            "message": "TikTokLive not installed. Running in simulation mode. Use 'Add Test Question' to add questions manually.",
            "username": username,
            "tiktok_available": False
        }
    
    # Stop existing thread if any
    if tiktok_thread and tiktok_thread.is_alive():
        if tiktok_client:
            try:
                asyncio.run(tiktok_client.stop())
            except:
                pass
    
    # Start TikTok client in a new thread
    tiktok_thread = threading.Thread(target=run_tiktok_client_in_thread, args=(username,), daemon=True)
    tiktok_thread.start()
    
    # Wait a moment for connection
    time.sleep(2)
    
    if question_queue.error_message:
        return {
            "status": "error",
            "message": question_queue.error_message,
            "username": username,
            "tiktok_available": True
        }
    
    return {
        "status": "connecting" if not question_queue.is_connected else "connected",
        "message": f"{'Connected' if question_queue.is_connected else 'Connecting'} to @{username}'s TikTok live stream...",
        "username": username,
        "tiktok_available": True
    }


@app.post("/disconnect")
def disconnect_from_stream():
    """Disconnect from the current TikTok stream."""
    global tiktok_client
    
    if tiktok_client:
        try:
            # Create a new loop to stop the client
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(tiktok_client.stop())
            loop.close()
        except Exception as e:
            print(f"Error stopping TikTok client: {e}")
        tiktok_client = None
    
    question_queue.is_connected = False
    question_queue.stream_username = ""
    question_queue.connection_time = None
    question_queue.error_message = ""
    
    return {"status": "disconnected", "message": "Disconnected from TikTok live stream"}


@app.post("/add-question")
def add_question(body: SimulateQuestionRequest):
    """Manually add a question (for simulation/testing)."""
    question_queue.add_question(body.username, body.question)
    return {
        "status": "added",
        "queue_size": len(question_queue.questions),
        "message": f"Question from @{body.username} added to queue"
    }


@app.get("/questions")
def get_questions():
    """Get all pending questions in the queue."""
    return {
        "questions": question_queue.get_all(),
        "count": len(question_queue.questions),
        "is_connected": question_queue.is_connected,
        "tiktok_available": question_queue.tiktok_available,
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
        "tiktok_available": question_queue.tiktok_available,
        "error_message": question_queue.error_message,
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    # Check TikTokLive availability
    try:
        from TikTokLive import TikTokLiveClient
        tiktok_installed = True
    except ImportError:
        tiktok_installed = False
    
    return {
        "status": "ok",
        "service": "TikTok Live Integration",
        "characters": list(CHARACTERS.keys()),
        "tiktok_installed": tiktok_installed,
        "is_connected": question_queue.is_connected,
        "queue_size": len(question_queue.questions),
    }
