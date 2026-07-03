"""The Ageing step implements the official MgT 2022 Ageing table.

A single 2D roll minus the total number of terms served selects a graded
result row; reductions land on the physical characteristics (and Intelligence
on the worst row). These tests pin the table rows and the roll/DM path.
"""

import pytest

from src.character import Character
from src.terms.base import StepStatus
from src.terms.careers.aging import (
    AGING_TRIGGER_AGE,
    AGING_WORST_TOTAL,
    AgingStep,
    _aging_reductions,
    _assign_targets,
)


def _character(age: int = AGING_TRIGGER_AGE, **stats: int) -> Character:
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
    char.age = age
    return char


def _with_terms(char: Character, terms: int, career: str = "Navy") -> Character:
    for _ in range(terms):
        char.record_career_term(career)
    return char


def _run(char: Character) -> AgingStep:
    step = AgingStep(char)
    step.resolve()
    step.apply()
    return step


# --- The table itself -----------------------------------------------------


def test_aging_reductions_match_rulebook_rows():
    assert _aging_reductions(3) == []
    assert _aging_reductions(1) == []  # 1+ is "No effect"
    assert _aging_reductions(0) == [("physical", 1)]
    assert _aging_reductions(-1) == [("physical", 1), ("physical", 1)]
    assert _aging_reductions(-2) == [("physical", 1)] * 3
    assert _aging_reductions(-3) == [("physical", 2), ("physical", 1), ("physical", 1)]
    assert _aging_reductions(-4) == [("physical", 2), ("physical", 2), ("physical", 1)]
    assert _aging_reductions(-5) == [("physical", 2)] * 3
    assert _aging_reductions(-6) == [
        ("physical", 2),
        ("physical", 2),
        ("physical", 2),
        ("mental", 1),
    ]


def test_totals_below_worst_row_clamp_to_worst():
    assert _aging_reductions(-9) == _aging_reductions(AGING_WORST_TOTAL)


def test_assign_targets_names_physical_then_intelligence():
    assert _assign_targets(_aging_reductions(-3)) == [
        ("Strength", 2),
        ("Dexterity", 1),
        ("Endurance", 1),
    ]
    assert _assign_targets(_aging_reductions(-6)) == [
        ("Strength", 2),
        ("Dexterity", 2),
        ("Endurance", 2),
        ("Intelligence", 1),
    ]


# --- The step: single 2D roll with a -(terms served) DM -------------------


def test_high_effective_total_has_no_effect(monkeypatch):
    monkeypatch.setattr("src.terms.careers.aging.roll", lambda _n: 12)
    char = _with_terms(_character(), 4)  # 12 - 4 = 8 → no effect

    step = _run(char)

    assert step.outcome.status == StepStatus.AGED
    assert "No effect" in step.outcome.description
    assert char.characteristics["Strength"].value == 7
    assert char.characteristics["Endurance"].value == 7


def test_low_effective_total_reduces_multiple_characteristics(monkeypatch):
    monkeypatch.setattr("src.terms.careers.aging.roll", lambda _n: 2)
    char = _with_terms(_character(), 8)  # 2 - 8 = -6 → worst row

    step = _run(char)

    assert step.outcome.status == StepStatus.AGED
    assert char.characteristics["Strength"].value == 5
    assert char.characteristics["Dexterity"].value == 5
    assert char.characteristics["Endurance"].value == 5
    assert char.characteristics["Intelligence"].value == 6
    assert step.outcome.data["effective_total"] == -6


def test_dm_is_negative_total_terms_served(monkeypatch):
    monkeypatch.setattr("src.terms.careers.aging.roll", lambda _n: 7)
    char = _character()
    _with_terms(char, 2, career="Navy")
    _with_terms(char, 3, career="Scout")  # 5 terms total across careers

    step = _run(char)

    assert step.outcome.data["terms_served"] == 5
    assert step.outcome.data["effective_total"] == 2  # 7 - 5 → 0 row


def test_reducing_a_characteristic_to_zero_triggers_crisis(monkeypatch):
    monkeypatch.setattr("src.terms.careers.aging.roll", lambda _n: 2)
    char = _with_terms(_character(Strength=2), 8)  # -6 row → Strength 2 - 2 = 0

    step = _run(char)

    assert char.characteristics["Strength"].value == 0
    assert step.outcome.status == StepStatus.AGING_CRISIS
    assert step.outcome.data["death"] is True


def test_below_trigger_age_reports_no_aging():
    char = _character(age=AGING_TRIGGER_AGE - 1)

    step = _run(char)

    assert step.outcome.status == StepStatus.NO_AGING
    assert char.characteristics["Strength"].value == 7


def test_seeded_roll_applies_the_matching_table_row(seeded_rng):
    char = _with_terms(_character(), 6)

    step = _run(char)

    expected = _assign_targets(_aging_reductions(step.outcome.data["effective_total"]))
    assert step.outcome.data["effective_total"] == step.outcome.data["rolled"] - 6
    assert [
        (r["characteristic"], r["amount"]) for r in step.outcome.data["reductions"]
    ] == expected
