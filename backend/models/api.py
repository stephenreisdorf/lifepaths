"""Thin request/response schemas for the API layer."""

from pydantic import BaseModel

from models.session import SessionState
from models.character import CharacterSheet


# ---------------------------------------------------------------------------
# Session creation
# ---------------------------------------------------------------------------

class CreateSessionRequest(BaseModel):
    lifepath_config_id: str
    player_name: str | None = None
    character_name: str | None = None


class SessionResponse(BaseModel):
    session_id: str
    state: SessionState


# ---------------------------------------------------------------------------
# Event resolution — table roll
# ---------------------------------------------------------------------------

class RollEventRequest(BaseModel):
    roll_result: int


# ---------------------------------------------------------------------------
# Event resolution — choice
# ---------------------------------------------------------------------------

class ChooseEventRequest(BaseModel):
    choice_keys: list[str]


# ---------------------------------------------------------------------------
# Stage advance (for repeatable stages)
# ---------------------------------------------------------------------------

class AdvanceRequest(BaseModel):
    repeat_stage: bool = False


# ---------------------------------------------------------------------------
# Combined response after any event resolution or advance
# ---------------------------------------------------------------------------

class EventResolutionResponse(BaseModel):
    session_id: str
    state: SessionState
    character_sheet: CharacterSheet | None = None   # populated when session completes
