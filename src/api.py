from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.character import AssociateType
from src.connections import PartySession
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
party_sessions: dict[str, PartySession] = {}


class StartRequest(BaseModel):
    # Optional MgT 2022 rules toggles. Anagathics (anti-aging drugs) is off by
    # default; enabling it adds the start-of-term anagathics offer/upkeep.
    anagathics_enabled: bool = False


@app.post("/api/start")
def start(req: StartRequest | None = None) -> dict:
    """Create a new game session, resolve initial automatic steps, and return the first interactive prompt."""
    session_id = str(uuid4())
    req = req or StartRequest()
    game = GameSession(anagathics_enabled=req.anagathics_enabled)
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


class PartyStartRequest(BaseModel):
    traveller_names: list[str] = Field(min_length=2)
    anagathics_enabled: bool = False


@app.post("/api/party/start")
def start_party(req: PartyStartRequest) -> dict:
    """Create independent character flows coordinated as one party."""
    try:
        party = PartySession(
            req.traveller_names,
            anagathics_enabled=req.anagathics_enabled,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    party_id = str(uuid4())
    starts = party.start()
    party_sessions[party_id] = party
    return {
        "party_id": party_id,
        "members": [
            {
                "traveller_id": member_id,
                "name": member.character.name,
                **starts[member_id].model_dump(),
            }
            for member_id, member in party.members.items()
        ],
    }


class PartySubmitRequest(BaseModel):
    party_id: str
    traveller_id: str
    player_input: dict | None = None


@app.post("/api/party/submit")
def submit_party(req: PartySubmitRequest) -> dict:
    """Advance one Traveller in a party and expose their connection events."""
    party = _party(req.party_id)
    try:
        result = party.submit(req.traveller_id, req.player_input)
        events = party.events_for(req.traveller_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "traveller_id": req.traveller_id,
        **result.model_dump(),
        "connection_events": [event.model_dump() for event in events],
    }


class ConnectionProposalRequest(BaseModel):
    party_id: str
    proposer_id: str
    partner_id: str
    event_id: str
    skill: str
    relationship: AssociateType
    narrative: str = ""


@app.post("/api/party/connections/propose")
def propose_connection(req: ConnectionProposalRequest) -> dict:
    """Record the event owner's side of a proposed connection."""
    party = _party(req.party_id)
    try:
        proposal = party.propose_connection(
            proposer_id=req.proposer_id,
            partner_id=req.partner_id,
            event_id=req.event_id,
            skill=req.skill,
            relationship=req.relationship,
            narrative=req.narrative,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return proposal.model_dump()


class ConnectionAcceptanceRequest(BaseModel):
    party_id: str
    proposal_id: str
    partner_id: str
    skill: str
    relationship: AssociateType


@app.post("/api/party/connections/accept")
def accept_connection(req: ConnectionAcceptanceRequest) -> dict:
    """Record the partner's agreement and apply both connection benefits."""
    party = _party(req.party_id)
    try:
        connection = party.accept_connection(
            req.proposal_id,
            partner_id=req.partner_id,
            skill=req.skill,
            relationship=req.relationship,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "connection": connection.model_dump(),
        "characters": party.character_summaries(),
    }


def _party(party_id: str) -> PartySession:
    party = party_sessions.get(party_id)
    if party is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid party session. Call /api/party/start first.",
        )
    return party
