from src.character import AssociateType, Character, Characteristic, Skill
from src.character_summary import CharacterSummary


def _rich_character() -> Character:
    """A character exercising every field the summary serializes."""
    char = Character(
        name="Test",
        age=34,
        characteristics={
            "Strength": Characteristic(name="Strength", value=9),
        },
        skills={
            "Gun Combat": Skill(name="Gun Combat", specialties={}, base_rank=1),
        },
        cash=50000,
        possessions=["Weapon", "TAS Membership"],
    )
    char.grant_skill("Pilot", level=2, specialty="Small Craft")
    char.add_associate(
        "Marc",
        AssociateType.RIVAL,
        description="Old flame",
        source_event="event 5",
    )
    return char


def test_summary_shape_matches_wire_contract():
    """The serialized read model reproduces the exact API payload shape."""
    summary = CharacterSummary.from_character(_rich_character()).model_dump()

    assert summary == {
        "age": 34,
        "characteristics": {
            "Strength": {"value": 9, "modifier": 1},
        },
        "skills": {
            "Gun Combat": {"base_rank": 1, "specialties": {}},
            "Pilot": {"base_rank": 0, "specialties": {"Small Craft": 2}},
        },
        "associates": [
            {
                "name": "Marc",
                "type": "rival",
                "description": "Old flame",
                "source_event": "event 5",
            }
        ],
        "cash": 50000,
        "possessions": ["Weapon", "TAS Membership"],
    }


def test_summary_keys_are_stable_for_empty_character():
    """A freshly-minted character still serializes every top-level key."""
    char = Character(name="Traveller", characteristics={}, skills={})
    summary = CharacterSummary.from_character(char).model_dump()

    assert set(summary) == {
        "age",
        "characteristics",
        "skills",
        "associates",
        "cash",
        "possessions",
    }
    assert summary["characteristics"] == {}
    assert summary["associates"] == []
