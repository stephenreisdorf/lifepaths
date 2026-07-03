"""Pre-Career Education terms.

The phase sits between Childhood and Career Selection. ``PreCareerChoiceTerm``
offers the eligible institutions; choosing one hands off to ``UniversityTerm``
or ``MilitaryAcademyTerm``, and every path ultimately routes into the existing
career flow. Each term mirrors ``AssignmentChangeTerm``'s small step-keyed
dispatch table (step type → handler) rather than a central if-elif chain.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.career_loader import (
    filter_eligible_careers,
    get_available_careers,
    load_career,
)
from src.character import Character
from src.terms.base import DispatchTerm, Step, StepOutcome, StepStatus, Term
from src.terms.careers import BasicTrainingStep, try_apply_characteristic_bonus
from src.terms.education.config import (
    UNIVERSITY,
    academy_by_career,
)
from src.terms.education.steps import (
    AcademyGraduationStep,
    ChooseUniversitySkillsStep,
    EducationQualificationStep,
    UniversityGraduationStep,
)

if TYPE_CHECKING:
    from src.terms.context import CareerContext

# Study ages the character by one four-year term.
EDUCATION_TERM_YEARS = 4


def _career_selection_term(character: Character) -> "Term":
    """Build the standard Career Selection transition (today's default flow)."""
    from src.terms.careers import ChooseCareerStep, TransitionTerm

    careers = filter_eligible_careers(character, get_available_careers())
    return TransitionTerm(character, ChooseCareerStep(character, careers))


class PreCareerChoiceTerm(Term):
    """A single decision step: which pre-career institution (or skip)."""

    def __init__(self, character: Character, options: list[dict]) -> None:
        super().__init__(character)
        from src.terms.education.steps import ChoosePreCareerStep

        self.steps = [ChoosePreCareerStep(character, options)]

    def label(self) -> str:
        return "Pre-Career Education"

    def next_term(self, context: "CareerContext") -> "Term | None":
        inner = self.steps[0]
        if inner.outcome is None:
            return None
        choice = inner.outcome.data.get("choice")
        if choice == "university":
            return UniversityTerm(context.character)
        if isinstance(choice, str) and choice.startswith("academy:"):
            return MilitaryAcademyTerm(context.character, choice.split(":", 1)[1])
        # SKIP (or anything unrecognised) → straight to career selection.
        return _career_selection_term(context.character)


class UniversityTerm(DispatchTerm):
    """Attempt University: qualify, pick subjects, then attempt to graduate."""

    def __init__(self, character: Character) -> None:
        super().__init__(character)
        self.config = UNIVERSITY
        qualification = self.config["qualification"]
        # RAW: an additional +1 DM if Social Standing is high.
        social = character.characteristics.get("Social Standing")
        extra_dm = (
            1
            if social is not None
            and social.value >= qualification["soc_bonus_at"]
            else 0
        )
        self.steps = [
            EducationQualificationStep(
                character,
                qualification["characteristic"],
                qualification["target"],
                extra_dm=extra_dm,
            )
        ]
        self._graduated_qualification_dm: int = 0

    def label(self) -> str:
        return "University"

    def _after_qualification(self, step: Step) -> None:
        if step.outcome.status != StepStatus.QUALIFIED:
            self.outcome = StepOutcome(
                status=StepStatus.NOT_ADMITTED,
                description="Not admitted to University — proceed to a career.",
            )
            return
        self.steps.append(
            ChooseUniversitySkillsStep(self.character, self.config["skills"])
        )

    def _after_skills(self, step: Step) -> None:
        graduation = self.config["graduation"]
        self.steps.append(
            UniversityGraduationStep(
                self.character,
                major=step.outcome.data["major"],
                minor=step.outcome.data["minor"],
                characteristic=graduation["characteristic"],
                target=graduation["target"],
                honours_target=graduation["honours_target"],
                graduate_qualification_dm=self.config["graduate_qualification_dm"],
            )
        )

    def _after_graduation(self, step: Step) -> None:
        self.character.age += EDUCATION_TERM_YEARS
        self._graduated_qualification_dm = step.qualification_dm
        self.outcome = StepOutcome(
            status=StepStatus.EDUCATED,
            description=step.outcome.description,
            data={"qualification_dm": step.qualification_dm},
        )

    _STEP_HANDLERS = {
        EducationQualificationStep: _after_qualification,
        ChooseUniversitySkillsStep: _after_skills,
        UniversityGraduationStep: _after_graduation,
    }

    def next_term(self, context: "CareerContext") -> "Term | None":
        if self.outcome is None:
            return None
        # A university graduate carries a one-shot DM into their first career
        # qualification; consumed by TransitionTerm._after_choose_career.
        context.pre_career_qualification_dm = self._graduated_qualification_dm
        return _career_selection_term(context.character)


class MilitaryAcademyTerm(DispatchTerm):
    """Attempt a Military Academy tied to a specific service career.

    Graduating enters the service commissioned (officer rank 1) and
    auto-qualified; merely attending enters it as an enlisted recruit.
    """

    def __init__(self, character: Character, career: str) -> None:
        super().__init__(character)
        self.academy = academy_by_career(career)
        self.career_key = career
        self.career_data = load_career(career)
        qualification = self.academy["qualification"]
        self.steps = [
            EducationQualificationStep(
                character,
                qualification["characteristic"],
                qualification["target"],
            )
        ]
        self._graduated: bool = False

    def label(self) -> str:
        return self.academy["name"]

    def _after_qualification(self, step: Step) -> None:
        if step.outcome.status != StepStatus.QUALIFIED:
            self.outcome = StepOutcome(
                status=StepStatus.NOT_ADMITTED,
                description=(
                    f"Not admitted to the {self.academy['name']} — "
                    "proceed to a career."
                ),
            )
            return
        # Academy basic training: every service skill at level 0.
        self.steps.append(
            BasicTrainingStep(self.character, self.career_data.service_skills)
        )

    def _after_training(self, step: Step) -> None:
        graduation = self.academy["graduation"]
        self.steps.append(
            AcademyGraduationStep(
                self.character,
                self.academy["name"],
                graduation["characteristic"],
                graduation["target"],
                graduation["honours_target"],
            )
        )

    def _after_graduation(self, step: Step) -> None:
        self.character.age += EDUCATION_TERM_YEARS
        self._graduated = step.graduated
        self.outcome = StepOutcome(
            status=StepStatus.GRADUATED if step.graduated else StepStatus.ATTENDED,
            description=step.outcome.description,
            data={"graduated": step.graduated},
        )

    _STEP_HANDLERS = {
        EducationQualificationStep: _after_qualification,
        BasicTrainingStep: _after_training,
        AcademyGraduationStep: _after_graduation,
    }

    def _apply_officer_commission(self) -> None:
        """Commission the character as a rank-1 officer of the service."""
        record = self.character.ensure_career(self.career_key)
        record.commissioned = True
        record.rank = 1
        officer_ranks = self.career_data.officer_ranks_as_dicts()
        entry = next((r for r in officer_ranks if r.get("rank") == 1), None)
        if entry is not None:
            bonus = entry.get("bonus_skill")
            if bonus and not try_apply_characteristic_bonus(self.character, bonus):
                self.character.grant_skill(bonus, level=0)

    def next_term(self, context: "CareerContext") -> "Term | None":
        if self.outcome is None:
            return None
        from src.terms.careers import CareerTerm

        if self.outcome.status == StepStatus.NOT_ADMITTED:
            return _career_selection_term(context.character)

        # Admitted (graduated or merely attended) → enter the service career.
        context.current_career_data = self.career_data
        context.career_term_count = 0
        context.blocked_career = None
        context.current_assignment = None
        if self._graduated:
            self._apply_officer_commission()
        return CareerTerm(
            context.character,
            self.career_data,
            is_first_term=True,
            term_number=1,
            # Academy entry bypasses the normal qualification roll.
            force_auto_qualify=True,
        )
