from pydantic import BaseModel


class AttributeModifier(BaseModel):
    attribute: str    # e.g. "strength", "wealth_level"
    delta: int        # signed integer


class Feature(BaseModel):
    id: str
    name: str
    description: str
    category: str | None = None          # "skill", "trait", "contact", "injury", etc.
    source_stage_id: str | None = None
    source_event_id: str | None = None
