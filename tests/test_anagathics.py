"""Anagathics — anti-aging drugs (Mongoose Traveller 2022, Ageing).

Covers the SOC 10+ entry roll (including the natural-2 → Prisoner outcome and
the SOC gate), the 1D×Cr25000 per-term cost deducted from cash, and the
positive DM an active course contributes to the Ageing roll.
"""

import pytest

from src.character import AnagathicsCourse, Character
from src.terms.anagathics import (
    ANAGATHICS_COST_MULTIPLIER,
    attempt_start_anagathics,
)
from src.terms.careers.aging import AgingStep


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


def _with_terms(char: Character, terms: int, career: str = "Navy") -> Character:
    for _ in range(terms):
        char.record_career_term(career)
    return char


# --- The SOC 10+ entry roll (the "gate") ----------------------------------


def test_high_soc_passes_the_check_and_starts_a_course(monkeypatch):
    # SOC 12 → DM +2; rolled 9 → total 11 ≥ 10. Cost die → 3 × Cr25000.
    rolls = iter([9, 3])
    monkeypatch.setattr("src.terms.anagathics.roll", lambda _n: next(rolls))
    char = _character(**{"Social Standing": 12})

    result = attempt_start_anagathics(char)

    assert result.started is True
    assert result.to_prisoner is False
    assert char.anagathics is not None
    assert char.anagathics.active is True
    assert char.anagathics.terms_used == 1


def test_low_soc_fails_the_same_roll_no_course(monkeypatch):
    # Same rolled 9, but SOC 5 → DM -1; total 8 < 10. The SOC value gates it.
    monkeypatch.setattr("src.terms.anagathics.roll", lambda _n: 9)
    char = _character(**{"Social Standing": 5})

    result = attempt_start_anagathics(char)

    assert result.started is False
    assert result.to_prisoner is False
    assert char.anagathics is None
    assert char.cash == 0


def test_natural_two_routes_to_prisoner_without_starting(monkeypatch):
    monkeypatch.setattr("src.terms.anagathics.roll", lambda _n: 2)
    char = _character(**{"Social Standing": 15})  # even huge SOC can't save a nat 2

    result = attempt_start_anagathics(char)

    assert result.to_prisoner is True
    assert result.started is False
    assert char.anagathics is None
    assert char.cash == 0


# --- The recurring cost ----------------------------------------------------


def test_starting_deducts_one_die_times_25000(monkeypatch):
    rolls = iter([10, 4])  # entry roll, then the cost die
    monkeypatch.setattr("src.terms.anagathics.roll", lambda _n: next(rolls))
    char = _character(**{"Social Standing": 10})
    char.cash = 100000

    result = attempt_start_anagathics(char)

    assert result.cost == 4 * ANAGATHICS_COST_MULTIPLIER
    assert char.anagathics.total_cost == 100000
    assert char.cash == 0


def test_maintaining_charges_again_and_can_go_into_debt():
    char = _character()
    char.start_anagathics_course(cost=25000)  # cash 0 → -25000
    assert char.cash == -25000

    char.maintain_anagathics_course(cost=50000)

    assert char.cash == -75000
    assert char.anagathics.terms_used == 2
    assert char.anagathics.total_cost == 75000


def test_maintain_is_a_no_op_without_an_active_course():
    char = _character()
    char.maintain_anagathics_course(cost=25000)
    assert char.anagathics is None
    assert char.cash == 0


# --- Interaction with the Ageing roll -------------------------------------


def test_active_course_adds_positive_dm_offsetting_terms_served(monkeypatch):
    # 6 terms served would give 7 - 6 = 1 → no effect anyway; use a low roll so
    # the offset is what saves the character. Rolled 2, 6 terms → -4 without the
    # course; with terms_used=6 the effective total is 2 - 6 + 6 = 2 (no effect).
    monkeypatch.setattr("src.terms.careers.aging.roll", lambda _n: 2)
    char = _with_terms(_character(), 6)
    char.age = 50
    char.anagathics = AnagathicsCourse(terms_used=6, total_cost=150000)

    step = AgingStep(char)
    step.resolve()
    step.apply()

    assert step.outcome.data["anagathics_dm"] == 6
    assert step.outcome.data["effective_total"] == 2
    assert "anagathics" in step.outcome.description
    assert char.characteristics["Strength"].value == 7  # unaged


def test_without_the_course_the_same_roll_ages_the_character(monkeypatch):
    monkeypatch.setattr("src.terms.careers.aging.roll", lambda _n: 2)
    char = _with_terms(_character(), 6)  # 2 - 6 = -4 → three physical reductions
    char.age = 50

    step = AgingStep(char)
    step.resolve()
    step.apply()

    assert step.outcome.data["anagathics_dm"] == 0
    assert step.outcome.data["effective_total"] == -4
    assert char.characteristics["Strength"].value < 7


def test_discontinued_course_contributes_no_dm(monkeypatch):
    monkeypatch.setattr("src.terms.careers.aging.roll", lambda _n: 2)
    char = _with_terms(_character(), 6)
    char.age = 50
    char.anagathics = AnagathicsCourse(terms_used=6)
    char.stop_anagathics_course()

    step = AgingStep(char)
    step.resolve()
    step.apply()

    assert char.anagathics.active is False
    assert step.outcome.data["anagathics_dm"] == 0
    assert step.outcome.data["effective_total"] == -4
