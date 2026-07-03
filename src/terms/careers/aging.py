from __future__ import annotations

from src.character import Character
from src.terms.base import (
    Step,
    StepOutcome,
    StepPrompt,
    StepStatus,
    StepType,
)
from src.utilities import roll


# Ageing first triggers at age 34 (end of the fourth term) and every term
# thereafter — enforced by CareerTerm._finalize_term, checked defensively here.
AGING_TRIGGER_AGE = 34

# The physical characteristics ageing reduces, in the order the automatic step
# assigns "physical" reductions. The rulebook lets the player choose which
# characteristics take the hit; the engine picks deterministically.
PHYSICAL_CHARACTERISTICS = ("Strength", "Dexterity", "Endurance")
# The only row that reaches a mental characteristic (the -6 row) reduces one;
# the engine applies it to Intelligence.
MENTAL_CHARACTERISTIC = "Intelligence"

# Official Mongoose Traveller 2022 Ageing table. You roll 2D and subtract the
# total number of terms served in all careers; the effective total selects a
# row. Each reduction is a (category, amount) pair — "physical" reductions fill
# PHYSICAL_CHARACTERISTICS in order (a row never reduces the same physical
# twice), "mental" reductions hit Intelligence. An effective total of 1+ is
# "No effect" and has no row; totals at or below AGING_WORST_TOTAL use the
# worst row.
AGING_TABLE: dict[int, list[tuple[str, int]]] = {
    0: [("physical", 1)],
    -1: [("physical", 1), ("physical", 1)],
    -2: [("physical", 1), ("physical", 1), ("physical", 1)],
    -3: [("physical", 2), ("physical", 1), ("physical", 1)],
    -4: [("physical", 2), ("physical", 2), ("physical", 1)],
    -5: [("physical", 2), ("physical", 2), ("physical", 2)],
    -6: [("physical", 2), ("physical", 2), ("physical", 2), ("mental", 1)],
}
AGING_WORST_TOTAL = min(AGING_TABLE)


def _aging_reductions(effective_total: int) -> list[tuple[str, int]]:
    """Return the (category, amount) reductions for an effective 2D total."""
    if effective_total >= 1:
        return []
    return AGING_TABLE[max(effective_total, AGING_WORST_TOTAL)]


def _assign_targets(reductions: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """Map abstract (category, amount) reductions onto named characteristics.

    Physical reductions fill Strength, Dexterity, Endurance in order (each row
    reduces any given physical at most once); a mental reduction hits
    Intelligence.
    """
    targets: list[tuple[str, int]] = []
    physical = iter(PHYSICAL_CHARACTERISTICS)
    for category, amount in reductions:
        name = next(physical) if category == "physical" else MENTAL_CHARACTERISTIC
        targets.append((name, amount))
    return targets


class AgingStep(Step):
    """Roll for ageing at the end of a career term (age 34+).

    Rolls a single 2D and subtracts the total number of terms served across
    all careers, then resolves the effective total against the official Ageing
    table. Reductions are applied to the physical characteristics (and, on the
    worst row, Intelligence). If any affected characteristic reaches 0, the
    character suffers an ageing crisis.
    """

    step_id = "aging_roll"
    step_type = StepType.AUTOMATIC

    def __init__(self, character: Character) -> None:
        super().__init__(character)
        self._triggered = False
        self._terms_served = 0
        self._anagathics_dm = 0
        self._rolled = 0
        self._effective_total = 0
        self._targets: list[tuple[str, int]] = []

    def resolve(self, player_input: dict | None = None) -> None:
        if self.character.age < AGING_TRIGGER_AGE:
            self._triggered = False
            return
        self._triggered = True
        self._terms_served = sum(
            record.terms_served for record in self.character.careers.values()
        )
        # An active anagathics course adds a positive DM equal to the terms it
        # has run, offsetting the -(terms served) penalty (Core Rulebook).
        self._anagathics_dm = self.character.anagathics_aging_dm()
        self._rolled = roll(2)
        self._effective_total = self._rolled - self._terms_served + self._anagathics_dm
        self._targets = _assign_targets(_aging_reductions(self._effective_total))

    def apply(self) -> None:
        if not self._triggered:
            self.outcome = StepOutcome(
                status=StepStatus.NO_AGING,
                description=f"Age {self.character.age} — no aging effects.",
            )
            return

        applied: list[str] = []
        for name, amount in self._targets:
            stat = self.character.characteristics.get(name)
            if stat is not None:
                self.character.add_characteristic(name, max(0, stat.value - amount))
            applied.append(f"{name} -{amount}")

        death = any(
            self.character.characteristics.get(name) is not None
            and self.character.characteristics[name].value <= 0
            for name in (*PHYSICAL_CHARACTERISTICS, MENTAL_CHARACTERISTIC)
        )

        roll_line = (
            f"Rolled {self._rolled} - {self._terms_served} terms served "
            f"= {self._effective_total}"
        )
        if self._anagathics_dm:
            roll_line = (
                f"Rolled {self._rolled} - {self._terms_served} terms served "
                f"+ {self._anagathics_dm} anagathics = {self._effective_total}"
            )
        desc_lines = [f"Aging (age {self.character.age}): {roll_line}"]
        if applied:
            desc_lines.append("  " + ", ".join(applied))
        else:
            desc_lines.append("  No effect")
        if death:
            desc_lines.append("  A characteristic has reached 0 — aging crisis!")

        self.outcome = StepOutcome(
            status=StepStatus.AGING_CRISIS if death else StepStatus.AGED,
            description="\n".join(desc_lines),
            data={
                "age": self.character.age,
                "terms_served": self._terms_served,
                "anagathics_dm": self._anagathics_dm,
                "rolled": self._rolled,
                "effective_total": self._effective_total,
                "reductions": [
                    {"characteristic": name, "amount": amount}
                    for name, amount in self._targets
                ],
                "death": death,
            },
        )

    def prompt(self) -> StepPrompt:
        if self.outcome is not None:
            return StepPrompt(
                step_id=self.step_id,
                step_type=self.step_type,
                description=self.outcome.description,
            )
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description="Rolling for aging effects...",
        )
