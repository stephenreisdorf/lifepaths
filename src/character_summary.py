"""API read model for a Character.

This is the single place that defines the serialized shape of a character for
API responses. Keeping it here — rather than hand-serializing in the engine —
means the engine no longer reaches into `Characteristic` / `Skill` / `Associate`
internals, and a new field surfaces by being added to one read model instead of
drifting silently until the engine is also edited.
"""

from pydantic import BaseModel

from src.character import Character


class CharacteristicView(BaseModel):
    """Serialized characteristic: its value and derived dice modifier."""

    value: int
    modifier: int


class SkillView(BaseModel):
    """Serialized skill: base rank and specialties flattened to name→rank."""

    base_rank: int
    specialties: dict[str, int]


class AssociateView(BaseModel):
    """Serialized associate (Contact / Ally / Rival / Enemy)."""

    name: str
    type: str
    description: str
    source_event: str | None


class CharacterSummary(BaseModel):
    """The API-facing snapshot of a character's current state.

    Construct via `from_character`; serialize with `model_dump()` to feed the
    `SubmitResult.character` payload.
    """

    age: int
    characteristics: dict[str, CharacteristicView]
    skills: dict[str, SkillView]
    associates: list[AssociateView]
    cash: int
    possessions: list[str]

    @classmethod
    def from_character(cls, character: Character) -> "CharacterSummary":
        """Build the read model from the domain `Character`."""
        return cls(
            age=character.age,
            characteristics={
                name: CharacteristicView(value=c.value, modifier=c.modifier())
                for name, c in character.characteristics.items()
            },
            skills={
                name: SkillView(
                    base_rank=s.base_rank,
                    specialties={
                        sp_name: sp.rank for sp_name, sp in s.specialties.items()
                    },
                )
                for name, s in character.skills.items()
            },
            associates=[
                AssociateView(
                    name=a.name,
                    type=a.type.value,
                    description=a.description,
                    source_event=a.source_event,
                )
                for a in character.associates
            ],
            cash=character.cash,
            possessions=list(character.possessions),
        )
