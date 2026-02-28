import re

from pydantic import BaseModel, model_validator


# Matches expressions like: d6, 2d6, 3d8+2, 1d20-5, d100
_DICE_RE = re.compile(
    r"^(?P<count>\d+)?d(?P<sides>\d+)(?P<bonus>[+-]\d+)?$",
    re.IGNORECASE,
)


class DiceExpression(BaseModel):
    """Parses and validates a dice expression string, and enforces roll bounds."""

    expression: str       # e.g. "2d6", "1d20+3", "d8-1"
    count: int            # number of dice
    sides: int            # sides per die
    bonus: int            # flat modifier (may be negative)

    @model_validator(mode="before")
    @classmethod
    def parse_expression(cls, data: dict) -> dict:
        expr = data.get("expression", "")
        m = _DICE_RE.match(expr.strip())
        if not m:
            raise ValueError(
                f"Invalid dice expression '{expr}'. "
                "Expected format: [N]d<sides>[+/-<bonus>], e.g. '2d6', 'd20+3'."
            )
        data["count"] = int(m.group("count") or 1)
        data["sides"] = int(m.group("sides"))
        data["bonus"] = int(m.group("bonus") or 0)
        return data

    @property
    def minimum(self) -> int:
        """Lowest possible roll result (all dice show 1)."""
        return self.count + self.bonus

    @property
    def maximum(self) -> int:
        """Highest possible roll result (all dice show max)."""
        return self.count * self.sides + self.bonus

    def validate_roll(self, roll_result: int) -> None:
        """Raise ValueError if roll_result is outside the valid range."""
        if not (self.minimum <= roll_result <= self.maximum):
            raise ValueError(
                f"Roll result {roll_result} is out of range "
                f"[{self.minimum}, {self.maximum}] for '{self.expression}'."
            )

    @classmethod
    def from_str(cls, expression: str) -> "DiceExpression":
        return cls(expression=expression, count=0, sides=0, bonus=0)
