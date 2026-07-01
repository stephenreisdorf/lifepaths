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
    [(0, -2), (2, -2), (3, -1), (6, 0), (9, 1), (12, 2), (15, 3)],
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
