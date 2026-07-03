"""Anagathics — anti-aging drugs (Mongoose Traveller 2022, Ageing).

At the start of any career term a Traveller may start taking anagathics by
rolling **SOC 10+** (2D + the Social Standing DM). On a natural 2 the attempt
goes wrong and the Traveller is sent straight to the Prisoner career this term
instead. Starting the course costs **1D×Cr25000** per term of use, deducted
from cash (the Traveller may go into debt).

While maintained, the course adds the number of terms it has run as a positive
DM to the Ageing roll (see ``src/terms/careers/aging.py``), so the Traveller
"effectively does not age". This module owns the dice-driven entry roll and
cost; the persistent state and its Ageing DM live on ``Character``.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.character import Character
from src.utilities import roll

# RAW: "rolling SOC 10+"; a natural 2 sends the Traveller to Prisoner instead.
ANAGATHICS_SOC_TARGET = 10
ANAGATHICS_PRISONER_ROLL = 2
# RAW character-creation cost: 1D×Cr25000 for each term the drugs are used.
ANAGATHICS_COST_DICE = 1
ANAGATHICS_COST_MULTIPLIER = 25000
# The career a botched attempt (natural 2) routes into.
PRISONER_CAREER = "Prisoner"


@dataclass
class AnagathicsStartResult:
    """Outcome of an attempt to start a course of anagathics."""

    rolled: int
    soc_dm: int
    total: int
    started: bool
    to_prisoner: bool
    cost: int


def attempt_start_anagathics(character: Character) -> AnagathicsStartResult:
    """Roll to start a course of anagathics for `character` (SOC 10+ check).

    On a natural 2 the character does not start the course and should be routed
    to the Prisoner career this term (``to_prisoner``). Otherwise, a total of
    10+ (2D + SOC DM) starts the course, rolling and charging its 1D×Cr25000
    cost via ``Character.start_anagathics_course``. A miss leaves the character
    unchanged.
    """
    rolled = roll(2)
    soc = character.characteristics.get("Social Standing")
    soc_dm = soc.modifier() if soc is not None else 0
    total = rolled + soc_dm

    if rolled == ANAGATHICS_PRISONER_ROLL:
        return AnagathicsStartResult(
            rolled=rolled,
            soc_dm=soc_dm,
            total=total,
            started=False,
            to_prisoner=True,
            cost=0,
        )

    if total >= ANAGATHICS_SOC_TARGET:
        cost = roll(ANAGATHICS_COST_DICE) * ANAGATHICS_COST_MULTIPLIER
        character.start_anagathics_course(cost)
        return AnagathicsStartResult(
            rolled=rolled,
            soc_dm=soc_dm,
            total=total,
            started=True,
            to_prisoner=False,
            cost=cost,
        )

    return AnagathicsStartResult(
        rolled=rolled,
        soc_dm=soc_dm,
        total=total,
        started=False,
        to_prisoner=False,
        cost=0,
    )


def roll_anagathics_cost() -> int:
    """Roll this term's anagathics cost (1D×Cr25000)."""
    return roll(ANAGATHICS_COST_DICE) * ANAGATHICS_COST_MULTIPLIER


def maintain_anagathics(character: Character) -> int:
    """Charge one more term of an already-active course and return the cost.

    Rolls the 1D×Cr25000 term cost and extends the course via
    ``Character.maintain_anagathics_course`` (a no-op with no active course,
    in which case this returns the rolled cost but charges nothing). Keeps the
    dice here rather than on the pure ``Character``.
    """
    cost = roll_anagathics_cost()
    character.maintain_anagathics_course(cost)
    return cost
