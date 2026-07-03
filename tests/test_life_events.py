"""Life Events and Injury sub-tables (Mongoose Traveller 2022, pp. 48-49).

Events / mishaps that instruct "Roll on the Life Events / Injury table" now
apply real mechanical results. These tests pin the transcribed table rows and
the wiring through `apply_effects` and the event / mishap steps, using either
the seeded RNG or a queued-roll stub for determinism.
"""

import pytest

from src.character import AssociateType, Character
from src.terms.base import StepStatus
from src.terms.careers.steps import EventsRollStep, MishapRollStep
from src.terms.effects import apply_effects
from src.terms.life_events import (
    _injury_effects,
    resolve_injury,
    resolve_life_event,
)


@pytest.fixture
def force_rolls(monkeypatch):
    """Return a helper that makes `life_events.roll` return queued values.

    Each call to `roll(...)` (regardless of dice count) pops the next queued
    value, so tests can force a specific Life Events / Injury row.
    """

    def _install(values):
        it = iter(values)
        monkeypatch.setattr("src.terms.life_events.roll", lambda d=1: next(it))

    return _install


def _character(**stats: int) -> Character:
    base = {
        "Strength": 7,
        "Dexterity": 7,
        "Endurance": 7,
        "Intelligence": 7,
        "Education": 7,
        "Social Standing": 7,
    }
    base.update(stats)
    char = Character(name="Test", characteristics={}, skills={})
    for name, value in base.items():
        char.add_characteristic(characteristic=name, value=value)
    return char


# --- Injury table ---------------------------------------------------------


def test_injury_rows_match_rulebook():
    # Rows 3-6 are deterministic (no internal 1D reduction roll).
    assert _injury_effects(3) == [
        {"type": "characteristic", "name": "Strength", "delta": -2}
    ]
    assert _injury_effects(4) == [
        {"type": "characteristic", "name": "Strength", "delta": -2}
    ]
    assert _injury_effects(5) == [
        {"type": "characteristic", "name": "Strength", "delta": -1}
    ]
    assert _injury_effects(6) == []  # Lightly injured — no permanent effect.


def test_injury_nearly_killed_hits_all_three_physicals(force_rolls):
    force_rolls([3])  # the -1D reduction for Strength
    effects = _injury_effects(1)
    assert effects == [
        {"type": "characteristic", "name": "Strength", "delta": -3},
        {"type": "characteristic", "name": "Dexterity", "delta": -2},
        {"type": "characteristic", "name": "Endurance", "delta": -2},
    ]


def test_resolve_injury_take_lower_picks_more_severe_row(force_rolls):
    # Roll twice → [5, 2]; lower number is the worse injury, so row 2.
    force_rolls([5, 2, 4])  # two table rolls, then the row-2 -1D reduction
    result, label, effects = resolve_injury(rolls=2, take="lower")
    assert result == 2
    assert label == "Severely injured"
    assert effects == [{"type": "characteristic", "name": "Strength", "delta": -4}]


def test_injury_effect_reduces_characteristic_and_floors_at_zero(force_rolls):
    char = _character(Strength=1)
    force_rolls([2, 3])  # Injury table = 2 (severe), -1D reduction = 3
    descriptions = apply_effects(char, [{"type": "injury"}])
    assert char.characteristics["Strength"].value == 0  # floored, not negative
    assert descriptions == ["Injury (1D=2): Severely injured — Strength -3 (reduced to 0!)"]


# --- Life Events table ----------------------------------------------------


def test_life_event_new_contact_grants_contact(force_rolls):
    char = _character()
    force_rolls([7])
    result, summary, effects = resolve_life_event()
    assert result == 7
    apply_effects(char, effects)
    assert any(a.type == AssociateType.CONTACT for a in char.associates)


def test_life_event_sickness_chains_into_injury(force_rolls):
    char = _character()
    # 2D = 2 (Sickness or Injury) → Injury table = 5 (Injured, any physical -1).
    force_rolls([2, 5])
    descriptions = apply_effects(char, [{"type": "life_event"}])
    assert descriptions[0] == "Life Event (2D=2): Sickness or Injury"
    assert descriptions[1] == "Injury (1D=5): Injured — Strength -1"
    assert char.characteristics["Strength"].value == 6


def test_life_event_unusual_aliens_grants_science_and_contact(force_rolls):
    char = _character()
    force_rolls([12, 2])  # 2D = 12 (Unusual Event), 1D sub = 2 (Aliens)
    descriptions = apply_effects(char, [{"type": "life_event"}])
    assert char.skills["Science"].base_rank == 1
    assert any(a.name == "Alien contact" for a in char.associates)
    assert "Aliens" in descriptions[0]


# --- Betrayal (Life Event 8) ----------------------------------------------


def test_betrayal_converts_existing_ally_to_rival():
    char = _character()
    char.add_associate(name="Old Friend", type=AssociateType.ALLY)
    apply_effects(char, [{"type": "betrayal"}])
    friend = next(a for a in char.associates if a.name == "Old Friend")
    assert friend.type == AssociateType.RIVAL
    assert len(char.associates) == 1  # converted, not duplicated


def test_betrayal_without_friends_gains_a_rival():
    char = _character()
    apply_effects(char, [{"type": "betrayal"}])
    assert char.associates[0].type == AssociateType.RIVAL


# --- Wiring through the event / mishap steps ------------------------------


def test_events_step_applies_life_event_effect(seeded_rng):
    char = _character()
    events = {7: {"text": "Life Event.", "effects": [{"type": "life_event"}]}}
    step = EventsRollStep(char, events)
    # Force the 2d6 event roll to land on entry 7.
    while True:
        step = EventsRollStep(char, events)
        step.resolve()
        if step.event_roll == 7:
            break
    step.apply()
    assert step.outcome.status == StepStatus.EVENT
    assert any("Life Event" in line for line in step.outcome.data["effects_applied"])


def test_mishap_step_applies_injury_effect(seeded_rng):
    char = _character()
    mishaps = {1: {"text": "Injured.", "effects": [{"type": "injury", "rolls": 2, "take": "lower"}]}}
    step = MishapRollStep(char, mishaps)
    while True:
        step = MishapRollStep(char, mishaps)
        step.resolve()
        if step.mishap_roll == 1:
            break
    step.apply()
    assert step.outcome.status == StepStatus.MISHAP
    assert any("Injury" in line for line in step.outcome.data["effects_applied"])
