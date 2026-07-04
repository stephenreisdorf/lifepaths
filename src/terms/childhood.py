from __future__ import annotations

from typing import TYPE_CHECKING

from src.career_loader import filter_eligible_careers
from src.character import Character
from src.terms.base import Step, StepOutcome, StepPrompt, StepStatus, StepType, Term
from src.utilities import roll

if TYPE_CHECKING:
    from src.terms.context import CareerContext


class RollCharacteristicsStep(Step):
    """Roll 2d6 for each of the six core characteristics."""

    step_id = "roll_characteristics"
    step_type = StepType.AUTOMATIC

    CHARACTERISTIC_NAMES = [
        "Strength",
        "Dexterity",
        "Endurance",
        "Intelligence",
        "Education",
        "Social Standing",
    ]

    def resolve(self, player_input: dict | None = None) -> None:
        self.characteristics: dict[str, int] = {
            name: roll(2) for name in self.CHARACTERISTIC_NAMES
        }

    def apply(self) -> None:
        for characteristic, value in self.characteristics.items():
            self.character.add_characteristic(
                characteristic=characteristic, value=value
            )
        rolled = ", ".join(f"{name} {value}" for name, value in self.characteristics.items())
        self.outcome = StepOutcome(
            status=StepStatus.ROLLED,
            description=f"Rolled characteristics: {rolled}.",
            data={"characteristics": dict(self.characteristics)},
        )

    def prompt(self) -> StepPrompt:
        description = (
            self.outcome.description
            if self.outcome
            else "Roll 2d6 for each of the six core characteristics."
        )
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description=description,
        )


class ChooseBackgroundSkillsStep(Step):
    """Choose background skills based on the character's Education modifier."""

    step_id = "choose_background_skills"
    step_type = StepType.CHOICE

    SKILL_OPTIONS: list[str] = [
        "Admin",
        "Animals",
        "Art",
        "Athletics",
        "Carouse",
        "Drive",
        "Electronics",
        "Flyer",
        "Language",
        "Mechanic",
        "Medic",
        "Profession",
        "Science",
        "Seafarer",
        "Streetwise",
        "Survival",
        "Vacc Suit",
    ]

    def required_skill_count(self) -> int:
        """Return the number of background skills the player must choose (3 + EDU DM)."""
        education = self.character.characteristics["Education"]
        return 3 + education.modifier()

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
            description="Choose your background skills.",
            options=self.SKILL_OPTIONS,
            required_count=self.required_skill_count(),
        )

    def resolve(self, player_input: dict | None = None) -> None:
        if player_input is None:
            raise ValueError("Skill selections are required.")
        selections = player_input.get("selections", [])
        required_choices = self.required_skill_count()
        if len(selections) != required_choices:
            raise ValueError(
                f"You need to choose exactly {required_choices} skills (3 + EDU DM)!"
            )
        self._selections_pending: list[str] = selections

    def apply(self) -> None:
        for skill in self._selections_pending:
            self.character.grant_skill(skill, level=0)
        self.outcome = StepOutcome(
            status=StepStatus.SELECTED,
            description=f"Background skills: {', '.join(self._selections_pending)}.",
            data={"skills": list(self._selections_pending)},
        )


class ChildhoodTerm(Term):
    """The childhood term: roll characteristics, then choose background skills."""

    def __init__(self, character: Character) -> None:
        super().__init__(character)
        self.steps: list[Step] = [
            RollCharacteristicsStep(self.character),
            ChooseBackgroundSkillsStep(self.character),
        ]

    def label(self) -> str:
        return "Childhood"

    def next_term(self, context: "CareerContext") -> "Term | None":
        # Local imports to avoid circular references.
        from src.terms.careers import ChooseCareerStep, TransitionTerm
        from src.terms.education import PreCareerChoiceTerm, eligible_options

        # Offer pre-career education (University / Military Academy) when the
        # character is eligible for at least one institution; otherwise go
        # straight to career selection.
        options = eligible_options(context.character)
        if options:
            return PreCareerChoiceTerm(context.character, options)

        careers = filter_eligible_careers(
            context.character, context.careers.get_available()
        )
        return TransitionTerm(
            context.character, ChooseCareerStep(context.character, careers)
        )
