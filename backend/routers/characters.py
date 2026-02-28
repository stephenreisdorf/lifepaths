"""Characters router — placeholder for future character sheet persistence."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/characters", tags=["characters"])

# Character sheets are currently returned inline from session completion.
# This router is reserved for future endpoints such as:
#   GET /api/characters/{character_id}  — retrieve a persisted sheet
#   GET /api/characters               — list all finalized characters
