"""Unit tests for the career-entry text/selection parsers."""

from src.career_data import CharacteristicCheck
from src.character import Character
from src.terms.careers.parsers import best_qualification_option


def _character(**stats: int) -> Character:
    char = Character(name="Test", characteristics={}, skills={})
    for name, value in stats.items():
        char.add_characteristic(characteristic=name, value=value)
    return char


def test_best_qualification_option_picks_highest_dm():
    # Dexterity 12 (DM +2) beats Intelligence 6 (DM +0).
    char = _character(Dexterity=12, Intelligence=6)
    options = [
        CharacteristicCheck(characteristic="Dexterity", target=6),
        CharacteristicCheck(characteristic="Intelligence", target=5),
    ]

    characteristic, target = best_qualification_option(char, options)

    assert characteristic == "Dexterity"
    assert target == 6


def test_best_qualification_option_ranks_missing_characteristic_last():
    # The character has no Strength, so the Endurance option must win even
    # though the Strength option is listed first.
    char = _character(Endurance=6)
    options = [
        CharacteristicCheck(characteristic="Strength", target=8),
        CharacteristicCheck(characteristic="Endurance", target=7),
    ]

    characteristic, target = best_qualification_option(char, options)

    assert characteristic == "Endurance"
    assert target == 7
