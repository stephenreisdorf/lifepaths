from datetime import datetime

from pydantic import BaseModel

from models.shared import Feature


class StageHistorySummary(BaseModel):
    stage_id: str
    stage_name: str
    visit_number: int
    narrative_fragments: list[str]    # outcome descriptions for readable history
    attributes_gained: dict[str, int]
    skills_gained: dict[str, int]
    features_gained: list[str]        # feature names


class CharacterSheet(BaseModel):
    id: str
    session_id: str
    lifepath_config_id: str
    character_name: str | None
    player_name: str | None
    attributes: dict[str, int]
    skills: dict[str, int]
    features: list[Feature]
    age: int
    stage_history: list[StageHistorySummary]
    finalized_at: datetime
