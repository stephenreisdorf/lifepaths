"""Session management router — implements the API state machine."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from content.loader import get_config
from models.content import EventType
from models.api import (
    AdvanceRequest,
    ChooseEventRequest,
    CreateSessionRequest,
    EventResolutionResponse,
    RollEventRequest,
    SessionResponse,
)
from models.character import CharacterSheet, StageHistorySummary
from models.dice import DiceExpression
from models.session import (
    CharacterSession,
    EventResolvedEntry,
    EventSkippedEntry,
    SessionCompletedEntry,
    SessionStartedEntry,
    StageCompletedEntry,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

# In-memory session store (replace with a database layer later)
_sessions: dict[str, CharacterSession] = {}


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _get_session(session_id: str) -> CharacterSession:
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return _sessions[session_id]


def _save(session: CharacterSession) -> None:
    session.updated_at = _now()
    _sessions[session.id] = session


def _assemble_character_sheet(session: CharacterSession) -> CharacterSheet:
    """Build a CharacterSheet by replaying the session log."""
    config = get_config(session.lifepath_config_id)
    state = session.derive_state(stages=config.stages)

    # Build per-stage history summaries
    history: list[StageHistorySummary] = []
    current_stage_attrs: dict[str, int] = {}
    current_stage_features: list[str] = []
    current_stage_narratives: list[str] = []
    active_stage_id: str | None = None
    visit_numbers: dict[str, int] = {}

    for entry in session.log:
        if isinstance(entry, SessionStartedEntry):
            active_stage_id = entry.starting_stage_id
            current_stage_attrs = {}
            current_stage_features = []
            current_stage_narratives = []

        elif isinstance(entry, EventResolvedEntry):
            for mod in entry.attribute_modifiers:
                current_stage_attrs[mod.attribute] = (
                    current_stage_attrs.get(mod.attribute, 0) + mod.delta
                )
            current_stage_features.extend(f.name for f in entry.features_granted)
            # Find outcome description for narrative
            if active_stage_id and active_stage_id in config.stages:
                stage_def = config.stages[active_stage_id]
                for event_def in stage_def.events:
                    for outcome in event_def.outcomes:
                        if outcome.id == entry.outcome_id:
                            current_stage_narratives.append(outcome.description)

        elif isinstance(entry, StageCompletedEntry):
            visit_numbers[entry.stage_id] = entry.visit_number
            stage_name = (
                config.stages[entry.stage_id].name
                if entry.stage_id in config.stages
                else entry.stage_id
            )
            history.append(
                StageHistorySummary(
                    stage_id=entry.stage_id,
                    stage_name=stage_name,
                    visit_number=entry.visit_number,
                    narrative_fragments=list(current_stage_narratives),
                    attributes_gained=dict(current_stage_attrs),
                    features_gained=list(current_stage_features),
                )
            )
            active_stage_id = entry.next_stage_id
            current_stage_attrs = {}
            current_stage_features = []
            current_stage_narratives = []

    return CharacterSheet(
        id=str(uuid4()),
        session_id=session.id,
        lifepath_config_id=session.lifepath_config_id,
        character_name=session.character_name,
        player_name=session.player_name,
        attributes=state.current_attributes,
        features=state.current_features,
        age=state.current_age,
        stage_history=history,
        finalized_at=_now(),
    )


def _try_auto_advance(session: CharacterSession) -> CharacterSheet | None:
    """Resolve automatic events and advance non-repeatable stages until player
    input is required. Returns a CharacterSheet if the session just completed,
    else None."""
    config = get_config(session.lifepath_config_id)

    while True:
        state = session.derive_state(stages=config.stages)

        if state.status != "in_progress" or state.current_stage_id is None:
            break

        stage = config.stages.get(state.current_stage_id)
        if stage is None:
            break

        all_events_done = (
            state.pending_event_index >= len(stage.events)
            and not state.injected_event_ids
        )

        if all_events_done:
            # Repeatable stages wait for the /advance endpoint
            if stage.is_repeatable:
                break

            # Find next stage — use last next_stage_override within current stage
            next_stage_id: str | None = stage.default_next_stage_id
            for entry in reversed(session.log):
                if isinstance(entry, StageCompletedEntry):
                    break  # don't look past the previous stage boundary
                if isinstance(entry, EventResolvedEntry) and entry.next_stage_override is not None:
                    next_stage_id = entry.next_stage_override
                    break

            visit_number = state.stage_visit_counts.get(state.current_stage_id, 0) + 1
            session.log.append(
                StageCompletedEntry(
                    type="stage_completed",
                    timestamp=_now(),
                    stage_id=state.current_stage_id,
                    visit_number=visit_number,
                    next_stage_id=next_stage_id,
                )
            )

            if next_stage_id is None:
                session.log.append(SessionCompletedEntry(type="session_completed", timestamp=_now()))
                _save(session)
                return _assemble_character_sheet(session)

            # Continue the loop — the next stage may start with automatic events
            continue

        # Not all events done — check if next pending event is automatic
        if state.injected_event_ids:
            next_event_id = state.injected_event_ids[0]
            event = next((e for e in stage.events if e.id == next_event_id), None)
        else:
            event = (
                stage.events[state.pending_event_index]
                if state.pending_event_index < len(stage.events)
                else None
            )

        if event is None or event.event_type != EventType.AUTOMATIC or not event.outcomes:
            break  # waiting for player input (or unresolvable automatic event)

        # Auto-resolve the automatic event using its sole outcome
        outcome = event.outcomes[0]
        session.log.append(
            EventResolvedEntry(
                type="event_resolved",
                timestamp=_now(),
                stage_id=stage.id,
                event_id=event.id,
                outcome_id=outcome.id,
                attribute_modifiers=outcome.attribute_modifiers,
                features_granted=outcome.features_granted,
                injected_event_ids=list(outcome.triggers_events),
                next_stage_override=outcome.next_stage_override,
                context_updates=dict(outcome.context_updates),
            )
        )
        # Continue to check if stage is now done or more automatics exist

    _save(session)
    return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("", response_model=SessionResponse, status_code=201)
def create_session(body: CreateSessionRequest) -> SessionResponse:
    try:
        config = get_config(body.lifepath_config_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"LifePathConfig '{body.lifepath_config_id}' not found",
        )

    now = _now()
    session = CharacterSession(
        id=str(uuid4()),
        lifepath_config_id=config.id,
        player_name=body.player_name,
        character_name=body.character_name,
        created_at=now,
        updated_at=now,
        log=[
            SessionStartedEntry(
                type="session_started",
                timestamp=now,
                lifepath_config_id=config.id,
                starting_stage_id=config.starting_stage_id,
                base_attributes=dict(config.base_attributes),
            )
        ],
    )
    _save(session)
    return SessionResponse(session_id=session.id, state=session.derive_state(stages=config.stages))


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str) -> SessionResponse:
    session = _get_session(session_id)
    config = get_config(session.lifepath_config_id)
    return SessionResponse(session_id=session.id, state=session.derive_state(stages=config.stages))


@router.post("/{session_id}/events/{event_id}/roll", response_model=EventResolutionResponse)
def roll_event(session_id: str, event_id: str, body: RollEventRequest) -> EventResolutionResponse:
    session = _get_session(session_id)
    config = get_config(session.lifepath_config_id)
    state = session.derive_state(stages=config.stages)

    if state.status != "in_progress":
        raise HTTPException(status_code=409, detail="Session is not in progress")

    stage = config.stages.get(state.current_stage_id or "")
    if stage is None:
        raise HTTPException(status_code=409, detail="No current stage")

    event_def = next((e for e in stage.events if e.id == event_id), None)
    if event_def is None:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found in current stage")

    if event_def.dice_expression is None:
        raise HTTPException(status_code=422, detail="Event does not support dice rolls")

    dice = DiceExpression.from_str(event_def.dice_expression)
    try:
        dice.validate_roll(body.roll_result)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    outcome = next(
        (
            o for o in event_def.outcomes
            if o.roll_min is not None
            and o.roll_max is not None
            and o.roll_min <= body.roll_result <= o.roll_max
        ),
        None,
    )
    if outcome is None:
        raise HTTPException(
            status_code=422,
            detail=f"No outcome matched roll result {body.roll_result} for event '{event_id}'",
        )

    session.log.append(
        EventResolvedEntry(
            type="event_resolved",
            timestamp=_now(),
            stage_id=stage.id,
            event_id=event_id,
            outcome_id=outcome.id,
            roll_value=body.roll_result,
            attribute_modifiers=outcome.attribute_modifiers,
            features_granted=outcome.features_granted,
            injected_event_ids=list(outcome.triggers_events),
            next_stage_override=outcome.next_stage_override,
            context_updates=dict(outcome.context_updates),
        )
    )

    sheet = _try_auto_advance(session)
    new_state = session.derive_state(stages=config.stages)
    return EventResolutionResponse(session_id=session.id, state=new_state, character_sheet=sheet)


@router.post("/{session_id}/events/{event_id}/choose", response_model=EventResolutionResponse)
def choose_event(session_id: str, event_id: str, body: ChooseEventRequest) -> EventResolutionResponse:
    session = _get_session(session_id)
    config = get_config(session.lifepath_config_id)
    state = session.derive_state(stages=config.stages)

    if state.status != "in_progress":
        raise HTTPException(status_code=409, detail="Session is not in progress")

    stage = config.stages.get(state.current_stage_id or "")
    if stage is None:
        raise HTTPException(status_code=409, detail="No current stage")

    event_def = next((e for e in stage.events if e.id == event_id), None)
    if event_def is None:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found in current stage")

    if len(body.choice_keys) < event_def.min_choices or len(body.choice_keys) > event_def.max_choices:
        raise HTTPException(
            status_code=422,
            detail=f"Expected between {event_def.min_choices} and {event_def.max_choices} choices, "
                   f"got {len(body.choice_keys)}",
        )

    matched_outcomes = [
        o for o in event_def.outcomes if o.choice_key in body.choice_keys
    ]
    if len(matched_outcomes) != len(body.choice_keys):
        raise HTTPException(status_code=422, detail="One or more choice keys did not match any outcome")

    # Validate requires_context against the current session context
    for outcome in matched_outcomes:
        for ctx_key, allowed_values in outcome.requires_context.items():
            actual = state.resolved_context.get(ctx_key)
            if actual not in allowed_values:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Outcome '{outcome.id}' requires context "
                        f"'{ctx_key}' to be one of {allowed_values}, "
                        f"but current value is {actual!r}"
                    ),
                )

    # Aggregate effects across all chosen outcomes
    all_modifiers = [mod for o in matched_outcomes for mod in o.attribute_modifiers]
    all_features = [f for o in matched_outcomes for f in o.features_granted]
    all_injected = [eid for o in matched_outcomes for eid in o.triggers_events]
    next_stage_override = next((o.next_stage_override for o in matched_outcomes if o.next_stage_override), None)
    aggregate_context: dict[str, str] = {}
    for o in matched_outcomes:
        aggregate_context.update(o.context_updates)

    session.log.append(
        EventResolvedEntry(
            type="event_resolved",
            timestamp=_now(),
            stage_id=stage.id,
            event_id=event_id,
            outcome_id=matched_outcomes[0].id if len(matched_outcomes) == 1 else ",".join(o.id for o in matched_outcomes),
            choice_keys_selected=list(body.choice_keys),
            attribute_modifiers=all_modifiers,
            features_granted=all_features,
            injected_event_ids=all_injected,
            next_stage_override=next_stage_override,
            context_updates=aggregate_context,
        )
    )

    sheet = _try_auto_advance(session)
    new_state = session.derive_state(stages=config.stages)
    return EventResolutionResponse(session_id=session.id, state=new_state, character_sheet=sheet)


@router.post("/{session_id}/events/{event_id}/skip", response_model=EventResolutionResponse)
def skip_event(session_id: str, event_id: str) -> EventResolutionResponse:
    session = _get_session(session_id)
    config = get_config(session.lifepath_config_id)
    state = session.derive_state(stages=config.stages)

    if state.status != "in_progress":
        raise HTTPException(status_code=409, detail="Session is not in progress")

    stage = config.stages.get(state.current_stage_id or "")
    if stage is None:
        raise HTTPException(status_code=409, detail="No current stage")

    event_def = next((e for e in stage.events if e.id == event_id), None)
    if event_def is None:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found in current stage")

    if not event_def.is_optional:
        raise HTTPException(status_code=422, detail=f"Event '{event_id}' is not optional and cannot be skipped")

    session.log.append(
        EventSkippedEntry(
            type="event_skipped",
            timestamp=_now(),
            stage_id=stage.id,
            event_id=event_id,
        )
    )

    sheet = _try_auto_advance(session)
    new_state = session.derive_state(stages=config.stages)
    return EventResolutionResponse(session_id=session.id, state=new_state, character_sheet=sheet)


@router.post("/{session_id}/advance", response_model=EventResolutionResponse)
def advance_session(session_id: str, body: AdvanceRequest) -> EventResolutionResponse:
    """Called for repeatable stages where the player decides whether to repeat."""
    session = _get_session(session_id)
    config = get_config(session.lifepath_config_id)
    state = session.derive_state(stages=config.stages)

    if state.status != "in_progress":
        raise HTTPException(status_code=409, detail="Session is not in progress")

    stage = config.stages.get(state.current_stage_id or "")
    if stage is None:
        raise HTTPException(status_code=409, detail="No current stage")

    all_events_done = (
        state.pending_event_index >= len(stage.events)
        and not state.injected_event_ids
    )
    if not all_events_done:
        raise HTTPException(status_code=409, detail="Stage events are not yet complete")

    if not stage.is_repeatable:
        raise HTTPException(status_code=409, detail="Stage is not repeatable; it advances automatically")

    visit_count = state.stage_visit_counts.get(stage.id, 0)
    visit_number = visit_count + 1

    if body.repeat_stage:
        if stage.max_repeats is not None and visit_count >= stage.max_repeats:
            raise HTTPException(
                status_code=422,
                detail=f"Stage '{stage.id}' has reached its repeat limit of {stage.max_repeats}",
            )
        # Repeat: complete current visit and re-enter same stage
        session.log.append(
            StageCompletedEntry(
                type="stage_completed",
                timestamp=_now(),
                stage_id=stage.id,
                visit_number=visit_number,
                next_stage_id=stage.id,  # loop back
            )
        )
    else:
        # Move on to the default next stage
        next_stage_id = stage.default_next_stage_id
        session.log.append(
            StageCompletedEntry(
                type="stage_completed",
                timestamp=_now(),
                stage_id=stage.id,
                visit_number=visit_number,
                next_stage_id=next_stage_id,
            )
        )
        if next_stage_id is None:
            session.log.append(SessionCompletedEntry(type="session_completed", timestamp=_now()))
            _save(session)
            sheet = _assemble_character_sheet(session)
            new_state = session.derive_state(stages=config.stages)
            return EventResolutionResponse(session_id=session.id, state=new_state, character_sheet=sheet)

    _save(session)
    new_state = session.derive_state(stages=config.stages)
    return EventResolutionResponse(session_id=session.id, state=new_state, character_sheet=None)
