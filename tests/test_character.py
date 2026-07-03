import pytest

from src.character import SKILL_MAX_LEVEL, Character, Characteristic


def make_character(**characteristic_values: int) -> Character:
    """Build a minimal Character with the given characteristic values."""
    return Character(
        name="Test",
        characteristics={
            name: Characteristic(name=name, value=value)
            for name, value in characteristic_values.items()
        },
        skills={},
    )


@pytest.mark.parametrize(
    "value, expected",
    [
        # Full Core Rulebook DM table; 0 is the special-cased bottom rung (-3).
        (0, -3),
        (1, -2),
        (2, -2),
        (3, -1),
        (4, -1),
        (5, -1),
        (6, 0),
        (7, 0),
        (8, 0),
        (9, 1),
        (10, 1),
        (11, 1),
        (12, 2),
        (13, 2),
        (14, 2),
        (15, 3),
    ],
)
def test_modifier_arithmetic(value, expected):
    assert Characteristic(name="X", value=value).modifier() == expected


def test_grant_skill_bare_starts_at_one_then_increments():
    char = make_character(Intelligence=12, Education=12)
    char.grant_skill("Gun Combat")
    assert char.skills["Gun Combat"].base_rank == 1
    char.grant_skill("Gun Combat")
    assert char.skills["Gun Combat"].base_rank == 2


def test_grant_skill_explicit_level_raises_but_never_reduces():
    char = make_character(Intelligence=12, Education=12)
    char.grant_skill("Pilot", level=2)
    assert char.skills["Pilot"].base_rank == 2
    char.grant_skill("Pilot", level=1)  # lower than current — no reduction
    assert char.skills["Pilot"].base_rank == 2


def test_grant_skill_clamps_to_per_skill_cap():
    char = make_character(Intelligence=12, Education=12)
    char.grant_skill("Melee", level=99)
    assert char.skills["Melee"].base_rank == SKILL_MAX_LEVEL


def test_grant_skill_refuses_over_total_budget():
    # Cap = 3 * (INT + EDU) = 3 * (1 + 1) = 6 total skill levels.
    char = make_character(Intelligence=1, Education=1)
    assert char.total_skill_level_cap() == 6
    for i in range(4):
        char.grant_skill(f"Skill{i}", level=2)
    assert char.total_skill_levels() == 6
    # Budget exhausted — further grants are refused (RAW: wasted).
    char.grant_skill("Skill4", level=2)
    assert char.total_skill_levels() == 6
    assert char.skills["Skill4"].base_rank == 0


def test_grant_skill_level_zero_ensures_skill_exists_at_rank_zero():
    char = make_character(Intelligence=12, Education=12)
    char.grant_skill("Athletics", level=0)
    assert char.skills["Athletics"].base_rank == 0
    # Re-granting at level 0 never reduces an already-raised skill.
    char.grant_skill("Athletics")  # bare → rank 1
    char.grant_skill("Athletics", level=0)
    assert char.skills["Athletics"].base_rank == 1


def test_grant_skill_specialty_bare_and_explicit():
    char = make_character(Intelligence=12, Education=12)
    char.grant_skill("Gun Combat", specialty="Slug")  # bare → rank 1
    assert char.skills["Gun Combat"].specialties["Slug"].rank == 1
    char.grant_skill("Gun Combat", specialty="Slug")  # +1 → rank 2
    assert char.skills["Gun Combat"].specialties["Slug"].rank == 2
    char.grant_skill("Gun Combat", level=1, specialty="Slug")  # no reduction
    assert char.skills["Gun Combat"].specialties["Slug"].rank == 2
    # Parent skill's base rank is untouched by specialty grants.
    assert char.skills["Gun Combat"].base_rank == 0


def test_grant_skill_level_zero_ensures_specialty_exists():
    char = make_character(Intelligence=12, Education=12)
    char.grant_skill("Pilot", level=0, specialty="Spacecraft")
    assert char.skills["Pilot"].specialties["Spacecraft"].rank == 0


def test_grant_skill_specialty_respects_total_budget():
    # Cap = 3 * (1 + 1) = 6 total skill levels; specialty ranks count too.
    char = make_character(Intelligence=1, Education=1)
    for name in ("Gun Combat", "Melee", "Athletics"):
        char.grant_skill(name, level=2, specialty="Spec")
    assert char.total_skill_levels() == 6
    # Budget exhausted — a further specialty grant is refused, not created.
    char.grant_skill("Pilot", level=2, specialty="Spacecraft")
    assert char.total_skill_levels() == 6
    assert "Spacecraft" not in char.skills["Pilot"].specialties
