from enum import Enum
from pydantic import BaseModel, model_validator

from models.shared import AttributeModifier, Feature


class EventType(str, Enum):
    TABLE_ROLL = "table_roll"
    CHOICE     = "choice"
    AUTOMATIC  = "automatic"


class OutcomeDefinition(BaseModel):
    id: str
    label: str
    description: str
    roll_min: int | None = None           # TABLE_ROLL events
    roll_max: int | None = None
    choice_key: str | None = None         # CHOICE events
    attribute_modifiers: list[AttributeModifier] = []
    features_granted: list[Feature] = []
    next_stage_override: str | None = None
    triggers_events: list[str] = []       # inject follow-up event IDs into current stage


class EventDefinition(BaseModel):
    id: str
    name: str
    description: str
    event_type: EventType
    dice_expression: str | None = None
    choice_prompt: str | None = None
    min_choices: int = 1
    max_choices: int = 1
    outcomes: list[OutcomeDefinition] = []
    is_optional: bool = False


class StageDefinition(BaseModel):
    id: str
    name: str
    description: str
    order_hint: int | None = None
    events: list[EventDefinition] = []
    default_next_stage_id: str | None = None   # None = terminal
    is_repeatable: bool = False
    max_repeats: int | None = None
    repeat_prompt: str | None = None
    prerequisite_stage_ids: list[str] = []
    prerequisite_features: list[str] = []
    prerequisite_attribute_minimums: dict[str, int] = {}
    age_cost: int = 0


class LifePathConfig(BaseModel):
    id: str
    name: str
    version: str
    starting_stage_id: str
    stages: dict[str, StageDefinition]    # keyed by id for O(1) lookup
    base_attributes: dict[str, int] = {}

    @model_validator(mode="after")
    def validate_cross_references(self) -> "LifePathConfig":
        stage_ids = set(self.stages.keys())

        if self.starting_stage_id not in stage_ids:
            raise ValueError(
                f"starting_stage_id '{self.starting_stage_id}' not found in stages"
            )

        for stage_id, stage in self.stages.items():
            if stage.default_next_stage_id is not None and stage.default_next_stage_id not in stage_ids:
                raise ValueError(
                    f"Stage '{stage_id}' references unknown default_next_stage_id "
                    f"'{stage.default_next_stage_id}'"
                )
            for prereq in stage.prerequisite_stage_ids:
                if prereq not in stage_ids:
                    raise ValueError(
                        f"Stage '{stage_id}' has unknown prerequisite_stage_id '{prereq}'"
                    )
            for event in stage.events:
                for outcome in event.outcomes:
                    if outcome.next_stage_override is not None and outcome.next_stage_override not in stage_ids:
                        raise ValueError(
                            f"Outcome '{outcome.id}' in event '{event.id}' of stage '{stage_id}' "
                            f"references unknown next_stage_override '{outcome.next_stage_override}'"
                        )
                    for triggered_id in outcome.triggers_events:
                        event_ids_in_stage = {e.id for e in stage.events}
                        if triggered_id not in event_ids_in_stage:
                            raise ValueError(
                                f"Outcome '{outcome.id}' triggers unknown event '{triggered_id}' "
                                f"(must be an event within the same stage '{stage_id}')"
                            )

        return self
