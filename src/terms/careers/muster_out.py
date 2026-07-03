from __future__ import annotations

from typing import TYPE_CHECKING

from src.character import Character
from src.terms.base import (
    Step,
    StepOutcome,
    StepPrompt,
    StepStatus,
    StepType,
    Term,
)
from src.terms.careers.parsers import try_apply_characteristic_bonus
from src.utilities import roll

if TYPE_CHECKING:
    from src.terms.context import CareerContext


class MusterOutStep(Step):
    """One benefit roll during muster-out.

    The player chooses the Cash column or the Material Benefits column,
    then 1d6 is rolled (indexed 1..7 for a table length of 7; DMs clamp
    within the column length). Cash adds to `character.cash`; material
    entries parse as characteristic bumps, skills, associates, or
    generic possessions.
    """

    step_id = "muster_out_roll"
    step_type = StepType.CHOICE

    CASH = "Cash"
    BENEFITS = "Benefits"

    def __init__(
        self,
        character: Character,
        career_name: str,
        cash_table: list,
        material_table: list,
        roll_index: int,
        total_rolls: int,
        dm: int = 0,
    ) -> None:
        super().__init__(character)
        self.career_name = career_name
        self.cash_table = list(cash_table)
        self.material_table = list(material_table)
        self.roll_index = roll_index
        self.total_rolls = total_rolls
        self.dm = dm
        self._decision_pending: str | None = None
        self.roll_value: int | None = None

    def _options(self) -> list[str]:
        options: list[str] = []
        if self.cash_table:
            options.append(self.CASH)
        if self.material_table:
            options.append(self.BENEFITS)
        return options

    def prompt(self) -> StepPrompt:
        if self.outcome is not None:
            return StepPrompt(
                step_id=self.step_id,
                step_type=self.step_type,
                description=self.outcome.description,
            )
        header = (
            f"Muster-out benefit roll {self.roll_index} of {self.total_rolls} "
            f"from the {self.career_name}. Pick Cash or Benefits, then roll 1d6"
            + (f" {self.dm:+d}" if self.dm else "")
            + "."
        )
        cash_preview = ", ".join(f"{i + 1}: {v}" for i, v in enumerate(self.cash_table))
        mat_preview = ", ".join(
            f"{i + 1}: {v}" for i, v in enumerate(self.material_table)
        )
        description = (
            f"{header}\n"
            f"Cash column — {cash_preview}.\n"
            f"Benefits column — {mat_preview}."
        )
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description=description,
            options=self._options(),
            required_count=1,
            data={
                "cash_table": self.cash_table,
                "material_table": self.material_table,
                "roll_index": self.roll_index,
                "total_rolls": self.total_rolls,
                "dm": self.dm,
            },
        )

    def resolve(self, player_input: dict | None = None) -> None:
        if player_input is None:
            raise ValueError("Muster-out column selection is required.")
        selections = player_input.get("selections", [])
        if len(selections) != 1:
            raise ValueError("Must choose a single muster-out column.")
        decision = selections[0]
        if decision not in self._options():
            raise ValueError(f"Unknown muster-out option: {decision}")
        self._decision_pending = decision
        self.raw_roll: int = roll(1)
        self.roll_value = self.raw_roll + self.dm

    def _table_entry(self, table: list) -> tuple[int, object]:
        """Clamp the rolled index into [1, len(table)] and return (index, entry)."""
        if not table:
            return 0, ""
        idx = max(1, min(len(table), self.roll_value or 1))
        return idx, table[idx - 1]

    def apply(self) -> None:
        assert self._decision_pending is not None and self.roll_value is not None
        if self._decision_pending == self.CASH:
            idx, entry = self._table_entry(self.cash_table)
            amount = int(entry) if isinstance(entry, (int, str)) and str(entry).lstrip("-").isdigit() else 0
            self.character.cash += amount
            self.outcome = StepOutcome(
                status=StepStatus.CASH,
                description=(
                    f"Benefit roll {self.roll_index}/{self.total_rolls}: "
                    f"rolled {self.roll_value} on the Cash column — "
                    f"gained Cr{amount}."
                ),
                data={
                    "column": "cash",
                    "raw_roll": self.raw_roll,
                    "roll_value": self.roll_value,
                    "dm": self.dm,
                    "index": idx,
                    "amount": amount,
                },
            )
            return

        idx, entry = self._table_entry(self.material_table)
        entry_text = str(entry).strip()
        applied = self._apply_material(entry_text)
        self.outcome = StepOutcome(
            status=StepStatus.BENEFITS,
            description=(
                f"Benefit roll {self.roll_index}/{self.total_rolls}: "
                f"rolled {self.roll_value} on the Benefits column — "
                f"{entry_text} ({applied})."
            ),
            data={
                "column": "material",
                "raw_roll": self.raw_roll,
                "roll_value": self.roll_value,
                "dm": self.dm,
                "index": idx,
                "entry": entry_text,
                "applied": applied,
            },
        )

    def _apply_material(self, entry: str) -> str:
        """Apply a material-column entry; return a short applied-description."""
        if not entry:
            return "nothing"
        # Characteristic bump like "Intelligence +1".
        if try_apply_characteristic_bonus(self.character, entry):
            return f"{entry} applied"
        # Associate: bare "Contact" / "Ally" / "Rival" / "Enemy".
        lowered = entry.lower()
        from src.character import AssociateType

        assoc_map = {
            "contact": AssociateType.CONTACT,
            "ally": AssociateType.ALLY,
            "rival": AssociateType.RIVAL,
            "enemy": AssociateType.ENEMY,
        }
        if lowered in assoc_map:
            self.character.add_associate(
                name=f"Muster-out {entry}",
                type=assoc_map[lowered],
                description=f"Gained during muster-out from the {self.career_name}.",
                source_event="muster_out",
            )
            return f"added {lowered}"
        # Fallback: treat as a possession (gear, membership, ship share, etc.).
        self.character.possessions.append(entry)
        return "added to possessions"


class MusterOutTerm(Term):
    """Sequence N benefit rolls at the end of a career.

    Roll count: one per term served in the career, plus a rank bonus of
    `(rank + 1) // 2` for any promotion beyond rank 0 (rank 1–2 = +1,
    rank 3–4 = +2, rank 5–6 = +3).
    """

    def __init__(
        self,
        character: Character,
        career_name: str,
        benefits: dict,
        terms_served: int,
        rank: int,
    ) -> None:
        super().__init__(character)
        self.career_name = career_name
        self.benefits = benefits or {}
        self.terms_served = terms_served
        self.rank = rank
        self.total_rolls = self._compute_total_rolls(terms_served, rank)
        cash = list(self.benefits.get("cash", []) or [])
        material = list(self.benefits.get("material", []) or [])
        for i in range(self.total_rolls):
            self.steps.append(
                MusterOutStep(
                    character=character,
                    career_name=career_name,
                    cash_table=cash,
                    material_table=material,
                    roll_index=i + 1,
                    total_rolls=self.total_rolls,
                )
            )

    @staticmethod
    def _compute_total_rolls(terms_served: int, rank: int) -> int:
        """Base one per term, plus one per two ranks attained (clamped at 0)."""
        base = max(0, terms_served)
        rank_bonus = 0 if rank <= 0 else (rank + 1) // 2
        return base + rank_bonus

    def label(self) -> str:
        return f"{self.career_name} — Muster Out"

    def advance(self) -> None:
        super().advance()
        if self.current_step_index >= len(self.steps):
            self.outcome = StepOutcome(
                status=StepStatus.MUSTERED_OUT,
                description=(
                    f"Mustered out of the {self.career_name} — "
                    f"{self.total_rolls} benefit roll(s) resolved."
                ),
            )

    def next_term(self, context: "CareerContext") -> "Term | None":
        # Muster-out completes character creation in the current flow.
        context.current_assignment = None
        return None


def _muster_out_term_for(
    context: "CareerContext", career_name: str
) -> "MusterOutTerm":
    """Build a MusterOutTerm for a career exit and clear the career context."""
    career_data = context.current_career_data
    benefits = career_data.benefits_as_dict() if career_data else {}
    record = context.character.careers.get(career_name)
    terms_served = record.terms_served if record else 0
    rank = record.rank if record else 0
    context.current_career_data = None
    context.current_assignment = None
    return MusterOutTerm(
        context.character,
        career_name=career_name,
        benefits=benefits,
        terms_served=terms_served,
        rank=rank,
    )
