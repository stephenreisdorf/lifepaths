"""Pre-Career Education steps.

The entry roll reuses ``PassFailRollStep``; the two graduation steps subclass
it but override ``apply()`` for their side effects (skill bumps and EDU gains
for University, honours flags for a Military Academy). Career entry that
follows a graduated academy is wired in the owning term's ``next_term``.
"""

from __future__ import annotations

from src.character import Character
from src.terms.base import (
    PassFailRollStep,
    Step,
    StepOutcome,
    StepPrompt,
    StepStatus,
    StepType,
)


class EducationQualificationStep(PassFailRollStep):
    """Entry roll for a University or Military Academy (2D + DM vs target)."""

    step_id = "education_qualification"
    check_label = "Entry"
    status_pass = StepStatus.QUALIFIED
    status_fail = StepStatus.FAILED


class ChoosePreCareerStep(Step):
    """Offer the eligible pre-career institutions plus a Skip-to-career option."""

    step_id = "choose_pre_career"
    step_type = StepType.CHOICE

    SKIP_LABEL = "Skip — go straight to a career"
    SKIP_KEY = "skip"

    def __init__(self, character: Character, options: list[dict]) -> None:
        super().__init__(character)
        # options: list of {"key", "label"} for eligible institutions.
        self.options = options

    def _labels(self) -> list[str]:
        return [o["label"] for o in self.options] + [self.SKIP_LABEL]

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
            description=(
                "Before choosing a career you may attempt pre-career "
                "education, or skip straight to a career."
            ),
            options=self._labels(),
            required_count=1,
        )

    def resolve(self, player_input: dict | None = None) -> None:
        if player_input is None:
            raise ValueError("A pre-career education choice is required.")
        selections = player_input.get("selections", [])
        if len(selections) != 1:
            raise ValueError("Must choose a single option.")
        label = selections[0]
        if label == self.SKIP_LABEL:
            self._choice_pending: str = self.SKIP_KEY
            return
        matching = [o for o in self.options if o["label"] == label]
        if not matching:
            raise ValueError(f"Unknown pre-career option: {label}")
        self._choice_pending = matching[0]["key"]

    def apply(self) -> None:
        if self._choice_pending == self.SKIP_KEY:
            self.outcome = StepOutcome(
                status=StepStatus.SKIP,
                description="Skipped pre-career education.",
                data={"choice": self.SKIP_KEY},
            )
            return
        label = next(
            o["label"] for o in self.options if o["key"] == self._choice_pending
        )
        self.outcome = StepOutcome(
            status=StepStatus.CHOSEN,
            description=f"Applying to {label}.",
            data={"choice": self._choice_pending, "label": label},
        )


class ChooseUniversitySkillsStep(Step):
    """Pick a major (gained at level 1) and a minor (gained at level 0)."""

    step_id = "choose_university_skills"
    step_type = StepType.CHOICE

    def __init__(self, character: Character, skills: list[str]) -> None:
        super().__init__(character)
        self.skills = skills

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
            description=(
                "Choose two subjects: the first is your major (gained at "
                "level 1), the second your minor (gained at level 0)."
            ),
            options=list(self.skills),
            required_count=2,
        )

    def resolve(self, player_input: dict | None = None) -> None:
        if player_input is None:
            raise ValueError("Major and minor selections are required.")
        selections = player_input.get("selections", [])
        if len(selections) != 2:
            raise ValueError("Must choose exactly two subjects (major, minor).")
        if selections[0] == selections[1]:
            raise ValueError("Major and minor must be different subjects.")
        for skill in selections:
            if skill not in self.skills:
                raise ValueError(f"Unknown subject: {skill}")
        self._major_pending: str = selections[0]
        self._minor_pending: str = selections[1]

    def apply(self) -> None:
        major, minor = self._major_pending, self._minor_pending
        self.character.grant_skill(major, level=1)
        self.character.grant_skill(minor, level=0)
        self.outcome = StepOutcome(
            status=StepStatus.SELECTED,
            description=f"Studying {major} (major) and {minor} (minor).",
            data={"major": major, "minor": minor},
        )


class UniversityGraduationStep(PassFailRollStep):
    """Resolve University graduation: on success bump major/minor and EDU."""

    step_id = "university_graduation"
    check_label = "Graduation"
    status_pass = StepStatus.GRADUATED
    status_fail = StepStatus.NOT_GRADUATED

    def __init__(
        self,
        character: Character,
        major: str,
        minor: str,
        characteristic: str,
        target: int,
        honours_target: int,
        graduate_qualification_dm: int,
    ) -> None:
        super().__init__(character, characteristic, target)
        self.major = major
        self.minor = minor
        self.honours_target = honours_target
        self.graduate_qualification_dm = graduate_qualification_dm
        # Read by the owning term to feed the next career qualification.
        self.graduated: bool = False
        self.honours: bool = False
        self.qualification_dm: int = 0

    def apply(self) -> None:
        self.graduated = self.total_roll >= self.target
        if not self.graduated:
            self.outcome = StepOutcome(
                status=self.status_fail,
                description=(
                    f"Graduation check on {self.check_characteristic}: rolled "
                    f"{self.total_roll} vs {self.target} — did not graduate "
                    "(entry skills retained)."
                ),
                data={"graduated": False},
            )
            return

        self.honours = self.total_roll >= self.honours_target
        # Major +1 (to level 2), minor +1 (to level 1), and EDU +1.
        self.character.grant_skill(self.major, level=None)
        self.character.grant_skill(self.minor, level=None)
        # RAW: graduation grants EDU +1 regardless of honours. Honours instead
        # grants a Commission roll (TODO: not yet modelled — see backlog).
        edu_gain = 1
        edu = self.character.characteristics["Education"]
        self.character.add_characteristic("Education", edu.value + edu_gain)
        self.qualification_dm = self.graduate_qualification_dm

        honours_note = " with honours" if self.honours else ""
        self.outcome = StepOutcome(
            status=self.status_pass,
            description=(
                f"Graduation check on {self.check_characteristic}: rolled "
                f"{self.total_roll} vs {self.target} — graduated{honours_note}! "
                f"{self.major} raised, {self.minor} raised, EDU +{edu_gain}."
            ),
            data={
                "graduated": True,
                "honours": self.honours,
                "edu_gain": edu_gain,
                "qualification_dm": self.qualification_dm,
            },
        )


class AcademyGraduationStep(PassFailRollStep):
    """Resolve Military Academy graduation.

    Career entry (commission, auto-qualify) is handled by the owning term's
    ``next_term``; this step records whether the character graduated and, on
    honours, grants EDU +1 and SOC +1.
    """

    step_id = "academy_graduation"
    check_label = "Graduation"
    status_pass = StepStatus.GRADUATED
    status_fail = StepStatus.NOT_GRADUATED

    def __init__(
        self,
        character: Character,
        academy_name: str,
        characteristic: str,
        target: int,
        honours_target: int,
    ) -> None:
        super().__init__(character, characteristic, target)
        self.academy_name = academy_name
        self.honours_target = honours_target
        self.graduated: bool = False
        self.honours: bool = False

    def apply(self) -> None:
        self.graduated = self.total_roll >= self.target
        if not self.graduated:
            self.outcome = StepOutcome(
                status=self.status_fail,
                description=(
                    f"Graduation check on {self.check_characteristic}: rolled "
                    f"{self.total_roll} vs {self.target} — did not graduate; "
                    "you still enter the service as an enlisted recruit."
                ),
                data={"graduated": False},
            )
            return

        self.honours = self.total_roll >= self.honours_target
        if self.honours:
            # RAW: Academy honours grant EDU +1 and SOC +1.
            edu = self.character.characteristics["Education"]
            self.character.add_characteristic("Education", edu.value + 1)
            soc = self.character.characteristics["Social Standing"]
            self.character.add_characteristic("Social Standing", soc.value + 1)
        honours_note = " with honours (EDU +1, SOC +1)" if self.honours else ""
        self.outcome = StepOutcome(
            status=self.status_pass,
            description=(
                f"Graduation check on {self.check_characteristic}: rolled "
                f"{self.total_roll} vs {self.target} — graduated{honours_note}! "
                "Commissioned as an officer on entry."
            ),
            data={"graduated": True, "honours": self.honours},
        )
