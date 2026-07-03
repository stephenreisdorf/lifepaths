"""Pre-Career Education data (University / Military Academy).

Numbers here are a faithful interpretation of the Traveller pre-career
education rules, centralised so they can be tuned without touching the step
machine. Each institution is a plain dict consumed by the education steps
and terms. Military academies map onto an existing service career: graduating
enters that career already commissioned and auto-qualified.
"""

from __future__ import annotations

from src.character import Character

# Skills offered by University (major at level 1, minor at level 0).
UNIVERSITY_SKILLS: list[str] = [
    "Admin",
    "Advocate",
    "Animals",
    "Art",
    "Astrogation",
    "Electronics",
    "Engineer",
    "Language",
    "Medic",
    "Navigation",
    "Profession",
    "Science",
]

UNIVERSITY: dict = {
    "name": "University",
    # Eligibility to apply.
    "eligibility": {"characteristic": "Education", "minimum": 6},
    # Entry roll: 2D + EDU DM (+1 more if INT >= int_bonus_at) vs target.
    "qualification": {
        "characteristic": "Education",
        "target": 7,
        "int_bonus_at": 9,
    },
    "skills": UNIVERSITY_SKILLS,
    # Graduation roll: 2D + EDU DM vs target; honours at honours_target.
    "graduation": {
        "characteristic": "Education",
        "target": 6,
        "honours_target": 10,
    },
    # One-shot DM applied to the first career qualification after graduating.
    "graduate_qualification_dm": 2,
}

# Each academy references a commissioned service career by its YAML key.
# Only services that define a commission / officer ranks in their career data
# are eligible — graduating enters the service as a rank-1 officer, which the
# career data must be able to represent.
MILITARY_ACADEMIES: list[dict] = [
    {
        "name": "Naval Academy",
        "career": "navy",
        "eligibility": {"characteristic": "Intelligence", "minimum": 6},
        "qualification": {"characteristic": "Intelligence", "target": 8},
        "graduation": {
            "characteristic": "Education",
            "target": 7,
            "honours_target": 11,
        },
    },
    {
        "name": "Military Academy (Army)",
        "career": "army",
        "eligibility": {"characteristic": "Endurance", "minimum": 6},
        "qualification": {"characteristic": "Endurance", "target": 7},
        "graduation": {
            "characteristic": "Education",
            "target": 7,
            "honours_target": 11,
        },
    },
    {
        "name": "Military Academy (Marines)",
        "career": "marine",
        "eligibility": {"characteristic": "Endurance", "minimum": 6},
        "qualification": {"characteristic": "Endurance", "target": 8},
        "graduation": {
            "characteristic": "Education",
            "target": 7,
            "honours_target": 11,
        },
    },
]


def _meets(character: Character, requirement: dict) -> bool:
    """Whether the character meets a `{characteristic, minimum}` requirement."""
    stat = character.characteristics.get(requirement["characteristic"])
    return stat is not None and stat.value >= requirement["minimum"]


def eligible_options(character: Character) -> list[dict]:
    """Return the pre-career institutions the character may apply to.

    Each entry is `{"key": ..., "label": ...}` where key is ``"university"``
    or ``"academy:<career>"``. The choice step appends its own Skip option.
    """
    options: list[dict] = []
    if _meets(character, UNIVERSITY["eligibility"]):
        options.append({"key": "university", "label": UNIVERSITY["name"]})
    for academy in MILITARY_ACADEMIES:
        if _meets(character, academy["eligibility"]):
            options.append(
                {"key": f"academy:{academy['career']}", "label": academy["name"]}
            )
    return options


def academy_by_career(career: str) -> dict:
    """Return the academy config whose service career matches `career`."""
    for academy in MILITARY_ACADEMIES:
        if academy["career"] == career:
            return academy
    raise KeyError(f"No military academy for career: {career}")
