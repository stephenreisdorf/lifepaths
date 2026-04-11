from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.engine import GameSession

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (keyed by session ID)
sessions: dict[str, GameSession] = {}


@app.post("/api/start")
def start() -> dict:
    """Create a new game session, resolve initial automatic steps, and return the first interactive prompt."""
    session_id = str(uuid4())
    game = GameSession()
    result = game.start()
    sessions[session_id] = game
    return {"session_id": session_id, **result.model_dump()}


class SubmitRequest(BaseModel):
    session_id: str
    player_input: dict | None = None


@app.post("/api/submit")
def submit(req: SubmitRequest) -> dict:
    """Submit player input for the current step and return the next prompt or final result."""
    game = sessions.get(req.session_id)
    if game is None:
        raise HTTPException(
            status_code=400, detail="Invalid session. Call /api/start first."
        )

    try:
        result = game.submit(req.player_input)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return result.model_dump()
