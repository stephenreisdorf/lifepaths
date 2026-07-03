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


AGING_TABLE = [
    {
        "min_age": 34,
        "max_age": 49,
        "checks": [
            {"characteristic": "Strength", "target": 8, "penalty": -1},
            {"characteristic": "Dexterity", "target": 7, "penalty": -1},
            {"characteristic": "Endurance", "target": 8, "penalty": -1},
        ],
    },
    {
        "min_age": 50,
        "max_age": 65,
        "checks": [
            {"characteristic": "Strength", "target": 9, "penalty": -1},
            {"characteristic": "Dexterity", "target": 8, "penalty": -1},
            {"characteristic": "Endurance", "target": 9, "penalty": -1},
        ],
    },
    {
        "min_age": 66,
        "max_age": 73,
        "checks": [
            {"characteristic": "Strength", "target": 9, "penalty": -2},
            {"characteristic": "Dexterity", "target": 8, "penalty": -2},
            {"characteristic": "Endurance", "target": 9, "penalty": -2},
            {"characteristic": "Intelligence", "target": 9, "penalty": -1},
        ],
    },
    {
        "min_age": 74,
        "max_age": 999,
        "checks": [
            {"characteristic": "Strength", "target": 9, "penalty": -2},
            {"characteristic": "Dexterity", "target": 9, "penalty": -2},
            {"characteristic": "Endurance", "target": 9, "penalty": -2},
            {"characteristic": "Intelligence", "target": 9, "penalty": -2},
        ],
    },
]


def _aging_bracket(age: int) -> dict | None:
    """Return the aging table bracket for the given age, or None if below 34."""
    for bracket in AGING_TABLE:
        if bracket["min_age"] <= age <= bracket["max_age"]:
            return bracket
    return None


class AgingStep(Step):
    """Roll aging checks at the end of a career term (age 34+).

    For each characteristic in the bracket, roll 2d6. Meeting or beating
    the target avoids damage; failing applies the penalty. If any
    physical characteristic or Intelligence reaches 0, the character is
    flagged as dead.
    """

    step_id = "aging_roll"
    step_type = StepType.AUTOMATIC

    def __init__(self, character: Character) -> None:
        super().__init__(character)
        self._bracket: dict | None = None
        self._results: list[dict] = []

    def resolve(self, player_input: dict | None = None) -> None:
        self._bracket = _aging_bracket(self.character.age)
        if self._bracket is None:
            return
        for check in self._bracket["checks"]:
            rolled = roll(2)
            passed = rolled >= check["target"]
            self._results.append({
                "characteristic": check["characteristic"],
                "target": check["target"],
                "penalty": check["penalty"],
                "rolled": rolled,
                "passed": passed,
            })

    def apply(self) -> None:
        if self._bracket is None:
            self.outcome = StepOutcome(
                status=StepStatus.NO_AGING,
                description=f"Age {self.character.age} — no aging effects.",
            )
            return

        applied: list[str] = []
        for result in self._results:
            if result["passed"]:
                applied.append(
                    f"{result['characteristic']}: rolled {result['rolled']} "
                    f"vs {result['target']} — no effect"
                )
            else:
                name = result["characteristic"]
                penalty = result["penalty"]
                stat = self.character.characteristics.get(name)
                if stat is not None:
                    new_value = max(0, stat.value + penalty)
                    self.character.add_characteristic(name, new_value)
                applied.append(
                    f"{result['characteristic']}: rolled {result['rolled']} "
                    f"vs {result['target']} — {result['penalty']:+d}"
                )

        death = any(
            self.character.characteristics.get(name) is not None
            and self.character.characteristics[name].value <= 0
            for name in ("Strength", "Dexterity", "Endurance", "Intelligence")
        )

        desc_lines = [f"Aging (age {self.character.age}):"]
        desc_lines.extend(f"  {line}" for line in applied)
        if death:
            desc_lines.append("  A characteristic has reached 0 — aging crisis!")

        self.outcome = StepOutcome(
            status=StepStatus.AGING_CRISIS if death else StepStatus.AGED,
            description="\n".join(desc_lines),
            data={
                "age": self.character.age,
                "results": self._results,
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
