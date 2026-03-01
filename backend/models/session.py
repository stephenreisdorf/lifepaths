from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from models.shared import AttributeModifier, Feature


# ---------------------------------------------------------------------------
# Log entry types
# ---------------------------------------------------------------------------

class SessionStartedEntry(BaseModel):
    type: Literal["session_started"] = "session_started"
    timestamp: datetime
    lifepath_config_id: str
    starting_stage_id: str
    base_attributes: dict[str, int]   # snapshot from LifePathConfig at creation time


class EventResolvedEntry(BaseModel):
    type: Literal["event_resolved"] = "event_resolved"
    timestamp: datetime
    stage_id: str
    event_id: str
    outcome_id: str
    # Resolution details (only one will be populated):
    roll_value: int | None = None
    choice_keys_selected: list[str] = []
    # Effect snapshots (self-contained history, no need to re-fetch definitions):
    attribute_modifiers: list[AttributeModifier] = []
    features_granted: list[Feature] = []
    # If this outcome injects follow-up events:
    injected_event_ids: list[str] = []
    # If this outcome overrides the next stage:
    next_stage_override: str | None = None
    context_updates: dict[str, str] = {}   # snapshotted from outcome(s) at resolve time


class EventSkippedEntry(BaseModel):
    type: Literal["event_skipped"] = "event_skipped"
    timestamp: datetime
    stage_id: str
    event_id: str                 # is_optional events only


class StageCompletedEntry(BaseModel):
    type: Literal["stage_completed"] = "stage_completed"
    timestamp: datetime
    stage_id: str
    visit_number: int             # 1 for first visit, 2+ for repeatable stages
    next_stage_id: str | None     # where the session is advancing to (None = terminal)


class SessionCompletedEntry(BaseModel):
    type: Literal["session_completed"] = "session_completed"
    timestamp: datetime


# Discriminated union — Pydantic uses the "type" field to pick the right model
SessionLogEntry = Annotated[
    SessionStartedEntry
    | EventResolvedEntry
    | EventSkippedEntry
    | StageCompletedEntry
    | SessionCompletedEntry,
    Field(discriminator="type")
]


# ---------------------------------------------------------------------------
# Derived state (computed by replaying the log)
# ---------------------------------------------------------------------------

class SessionState(BaseModel):
    """All current state derived from replaying a CharacterSession.log."""
    status: Literal["in_progress", "completed", "abandoned"]
    current_stage_id: str | None
    # Index into the current stage's events list.
    # Takes into account injected follow-up events from prior outcomes.
    pending_event_index: int
    # Queue of injected follow-up event IDs to resolve before advancing stage index:
    injected_event_ids: list[str]
    current_attributes: dict[str, int]
    current_features: list[Feature]
    current_age: int
    stage_visit_counts: dict[str, int]   # stage_id → completed visit count
    resolved_context: dict[str, str] = {}


# ---------------------------------------------------------------------------
# The session itself
# ---------------------------------------------------------------------------

class CharacterSession(BaseModel):
    id: str                     # UUID
    lifepath_config_id: str
    player_name: str | None = None
    character_name: str | None = None
    created_at: datetime
    updated_at: datetime

    # The log is the only mutable part — always append-only
    log: list[SessionLogEntry] = []

    def derive_state(self, stages: dict | None = None) -> SessionState:
        """Replay the log to compute current state from scratch.

        ``stages`` is the dict[str, StageDefinition] from LifePathConfig. It is
        only needed to look up ``age_cost`` when a StageCompletedEntry is
        encountered. Pass None (or omit) if age tracking is not required.
        """
        if not self.log:
            raise ValueError("Log is empty — session has no SessionStartedEntry")

        first = self.log[0]
        if not isinstance(first, SessionStartedEntry):
            raise ValueError("First log entry must be SessionStartedEntry")

        attributes: dict[str, int] = dict(first.base_attributes)
        features: list[Feature] = []
        stage_visit_counts: dict[str, int] = {}
        current_stage_id: str | None = first.starting_stage_id
        pending_event_index: int = 0
        injected_event_ids: list[str] = []
        current_age: int = 0
        status: Literal["in_progress", "completed", "abandoned"] = "in_progress"
        resolved_context: dict[str, str] = {}

        for entry in self.log[1:]:
            if isinstance(entry, EventResolvedEntry):
                for mod in entry.attribute_modifiers:
                    attributes[mod.attribute] = attributes.get(mod.attribute, 0) + mod.delta
                features.extend(entry.features_granted)
                resolved_context.update(entry.context_updates)
                # Prepend new injected events to the front of the queue
                injected_event_ids = list(entry.injected_event_ids) + injected_event_ids
                if injected_event_ids:
                    # Next resolution will drain one from the injected queue;
                    # don't advance the main index yet.
                    injected_event_ids.pop(0)
                else:
                    pending_event_index += 1

            elif isinstance(entry, EventSkippedEntry):
                pending_event_index += 1

            elif isinstance(entry, StageCompletedEntry):
                stage_visit_counts[entry.stage_id] = (
                    stage_visit_counts.get(entry.stage_id, 0) + 1
                )
                if stages and entry.stage_id in stages:
                    current_age += stages[entry.stage_id].age_cost
                current_stage_id = entry.next_stage_id
                pending_event_index = 0
                injected_event_ids = []

            elif isinstance(entry, SessionCompletedEntry):
                status = "completed"

        return SessionState(
            status=status,
            current_stage_id=current_stage_id,
            pending_event_index=pending_event_index,
            injected_event_ids=injected_event_ids,
            current_attributes=attributes,
            current_features=features,
            current_age=current_age,
            stage_visit_counts=stage_visit_counts,
            resolved_context=resolved_context,
        )
