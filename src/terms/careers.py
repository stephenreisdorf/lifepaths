from __future__ import annotations

from typing import TYPE_CHECKING

from src.character import Character
from src.terms.base import (
    PassFailRollStep,
    Step,
    StepOutcome,
    StepPrompt,
    StepType,
    Term,
)
from src.utilities import roll

if TYPE_CHECKING:
    from src.engine import GameSession


def try_apply_characteristic_bonus(character: Character, entry: str) -> bool:
    """If `entry` is '<Characteristic> +<N>', bump that characteristic.

    Returns True if the entry was consumed as a characteristic bonus, False
    if the caller should fall back to treating it as a skill. Used by both
    rank bonuses and skill-table rolls (Personal Development et al.).
    """
    parts = entry.rsplit(" +", 1)
    if len(parts) != 2 or not parts[1].isdigit():
        return False
    name, delta = parts[0], int(parts[1])
    if name not in character.characteristics:
        return False
    current = character.characteristics[name].value
    character.add_characteristic(name, current + delta)
    return True


class RollQualificationStep(PassFailRollStep):
    """Roll 2d6 + DM to see if you qualify for the career."""

    step_id = "roll_qualification"
    check_label = "Qualification"
    status_pass = "QUALIFIED"
    status_fail = "FAILED"


class BasicTrainingStep(Step):
    step_id = "basic_training"
    step_type = StepType.AUTOMATIC

    def __init__(self, character: Character, service_skills: list[str]):
        super().__init__(character=character)
        self.service_skills = service_skills

    def apply(self) -> None:
        for skill in self.service_skills:
            self.character.add_skill(skill)
        self.outcome = StepOutcome(
            status="TRAINED",
            description=(
                f"Gained basic training skills: {', '.join(self.service_skills)}."
            ),
            data={"service_skills": list(self.service_skills)},
        )


class ChooseAssignmentStep(Step):
    """Choose an assignment under the given career."""

    step_id = "choose_assignment"
    step_type = StepType.CHOICE

    def __init__(self, character: Character, assignments: list[dict]):
        super().__init__(character=character)
        self.assignments = assignments

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
            description="Choose your assignment.",
            options=[a["name"] for a in self.assignments],
            required_count=1,
        )

    def resolve(self, player_input: dict | None = None) -> None:
        if player_input is None:
            raise ValueError("Assignment selection is required.")
        selections = player_input.get("selections", [])
        if len(selections) != 1:
            raise ValueError("Must choose a single assignment")
        selected_name = selections[0]
        matching = [a for a in self.assignments if a["name"] == selected_name]
        if not matching:
            raise ValueError(f"Unknown assignment: {selected_name}")
        self._selected_assignment_pending: dict = matching[0]

    def apply(self) -> None:
        assignment = self._selected_assignment_pending
        self.outcome = StepOutcome(
            status="SELECTED",
            description=f"Assignment: {assignment['name']}.",
            data={"assignment": assignment, "name": assignment["name"]},
        )


class ChooseCareerSkillsTable(Step):
    """Choose which skill table to roll on."""

    step_id = "choose_career_skills_table"
    step_type = StepType.CHOICE

    def __init__(self, character: Character, skill_tables: list[str]):
        super().__init__(character=character)
        self.skill_tables = skill_tables

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
            description="Choose a skill table to roll on.",
            options=self.skill_tables,
            required_count=1,
        )

    def resolve(self, player_input: dict | None = None) -> None:
        if player_input is None:
            raise ValueError("Skill table selection is required.")
        selections = player_input.get("selections", [])
        if len(selections) != 1:
            raise ValueError("Must choose a single skill table.")
        self._selected_skill_table_pending: str = selections[0]

    def apply(self) -> None:
        table = self._selected_skill_table_pending
        self.outcome = StepOutcome(
            status="SELECTED",
            description=f"Skill table: {table}.",
            data={"skill_table": table},
        )


class RollForSkillStep(Step):
    step_id = "roll_for_skill"
    step_type = StepType.AUTOMATIC

    def __init__(self, character: Character, skill_options: list[str]):
        super().__init__(character=character)
        self.skill_options = skill_options

    def resolve(self, player_input: dict | None = None) -> None:
        self.skill_roll: int = roll(1)
        self.skill: str = self.skill_options[self.skill_roll - 1]

    def apply(self) -> None:
        # Skill tables can contain '<Characteristic> +<N>' entries that
        # should bump a characteristic rather than grant a skill.
        if not try_apply_characteristic_bonus(self.character, self.skill):
            self.character.increment_skill(self.skill, specialty="TODO")
        self.outcome = StepOutcome(
            status="ROLLED",
            description=(
                f"Rolled a {self.skill_roll} on the skill table — "
                f"gained {self.skill}."
            ),
            data={"skill": self.skill, "roll": self.skill_roll},
        )

    def prompt(self) -> StepPrompt:
        if self.outcome is not None:
            description = self.outcome.description
        else:
            description = "Roll d6 for a skill on the selected skill table."
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description=description,
        )


class SurvivalCheckStep(PassFailRollStep):
    """Roll 2d6 + DM vs the assignment's survival target.

    Per the rules, a natural 2 on the dice is always a failure, even if
    the modified total clears the target.
    """

    step_id = "survival_check"
    check_label = "Survival"
    status_pass = "SURVIVED"
    status_fail = "FAILED"

    def __init__(self, character: Character, assignment: dict) -> None:
        survival = assignment["survival"]
        super().__init__(
            character=character,
            check_characteristic=survival["characteristic"],
            target=survival["target"],
        )
        self.assignment = assignment

    def apply(self) -> None:
        passed = self.total_roll >= self.target and self.raw_roll != 2
        status = self.status_pass if passed else self.status_fail
        self.outcome = StepOutcome(
            status=status,
            description=self._post_description(status),
            data={
                "raw_roll": self.raw_roll,
                "total_roll": self.total_roll,
                "target": self.target,
                "modifier": self.modifier,
                "characteristic": self.check_characteristic,
                "natural_2_failure": self.raw_roll == 2
                and self.total_roll >= self.target,
            },
        )

    def _post_description(self, status: str) -> str:
        if status == self.status_fail and self.raw_roll == 2 and self.total_roll >= self.target:
            return (
                f"Survival check on {self.check_characteristic}: "
                f"rolled {self.total_roll} vs target {self.target} — "
                f"FAILED (natural 2)."
            )
        return super()._post_description(status)


class MishapRollStep(Step):
    """Roll d6 on the career's mishap table. Flavor text only — no mechanical effects applied."""

    step_id = "mishap_roll"
    step_type = StepType.AUTOMATIC

    def __init__(self, character: Character, mishaps: dict) -> None:
        super().__init__(character=character)
        self.mishaps = mishaps

    def resolve(self, player_input: dict | None = None) -> None:
        self.mishap_roll: int = roll(1)
        self.mishap_text: str = str(self.mishaps.get(self.mishap_roll, "")).strip()

    def apply(self) -> None:
        # Flavor-only for now; effects are not auto-applied.
        self.outcome = StepOutcome(
            status="MISHAP",
            description=(
                f"Mishap! Rolled {self.mishap_roll}: {self.mishap_text} "
                "Your career ends."
            ),
            data={"roll": self.mishap_roll, "text": self.mishap_text},
        )

    def prompt(self) -> StepPrompt:
        if self.outcome is not None:
            description = self.outcome.description
        else:
            description = "Roll d6 on the mishap table."
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description=description,
        )


class EventsRollStep(Step):
    """Roll 2d6 on the career's events table. Flavor text only — no mechanical effects applied."""

    step_id = "events_roll"
    step_type = StepType.AUTOMATIC

    def __init__(self, character: Character, events: dict) -> None:
        super().__init__(character=character)
        self.events = events

    def resolve(self, player_input: dict | None = None) -> None:
        self.event_roll: int = roll(2)
        self.event_text: str = str(self.events.get(self.event_roll, "")).strip()

    def apply(self) -> None:
        # Flavor-only for now; effects are not auto-applied.
        self.outcome = StepOutcome(
            status="EVENT",
            description=f"Event (2d6 = {self.event_roll}): {self.event_text}",
            data={"roll": self.event_roll, "text": self.event_text},
        )

    def prompt(self) -> StepPrompt:
        if self.outcome is not None:
            description = self.outcome.description
        else:
            description = "Roll 2d6 on the events table."
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description=description,
        )


class AdvancementRollStep(PassFailRollStep):
    """Roll 2d6 + DM vs the assignment's advancement target. On success, promote and apply rank bonus."""

    step_id = "advancement_roll"
    check_label = "Advancement"
    status_pass = "PROMOTED"
    status_fail = "NOT_PROMOTED"
    status_at_max_rank = "AT_MAX_RANK"

    def __init__(
        self,
        character: Character,
        career_name: str,
        assignment: dict,
        ranks: list[dict],
    ) -> None:
        advancement = assignment["advancement"]
        super().__init__(
            character=character,
            check_characteristic=advancement["characteristic"],
            target=advancement["target"],
        )
        self.career_name = career_name
        self.assignment = assignment
        self.ranks = ranks
        self.max_rank: int | None = (
            max(r["rank"] for r in ranks) if ranks else None
        )

    def apply(self) -> None:
        # Always tick terms_served at the end of a successful term.
        self.character.record_career_term(self.career_name)

        current_rank = self.character.careers.get(self.career_name)
        at_max = (
            self.max_rank is not None
            and current_rank is not None
            and current_rank.rank >= self.max_rank
        )

        if self.total_roll >= self.target:
            if at_max:
                # Successful roll but already at top of the rank ladder.
                status = self.status_at_max_rank
                self.new_rank_title: str | None = None
            else:
                record = self.character.promote(self.career_name)
                status = self.status_pass
                self.new_rank_title = self._apply_rank_bonus(record.rank)
        else:
            status = self.status_fail
            self.new_rank_title = None

        self.outcome = StepOutcome(
            status=status,
            description=self._post_description(status),
            data={
                "raw_roll": self.raw_roll,
                "total_roll": self.total_roll,
                "target": self.target,
                "modifier": self.modifier,
                "characteristic": self.check_characteristic,
                "new_rank_title": self.new_rank_title,
            },
        )

    def _post_description(self, status: str) -> str:
        if status == self.status_pass and self.new_rank_title:
            outcome_str = f"PROMOTED to {self.new_rank_title}"
        elif status == self.status_at_max_rank:
            outcome_str = "already at top rank — no promotion"
        else:
            outcome_str = status
        return (
            f"Advancement check on {self.check_characteristic}: "
            f"rolled {self.total_roll} vs target {self.target} — {outcome_str}."
        )

    def _apply_rank_bonus(self, new_rank: int) -> str | None:
        """Find the rank entry for new_rank, apply any bonus skill/characteristic, return the title."""
        entry = next((r for r in self.ranks if r.get("rank") == new_rank), None)
        if entry is None:
            return None
        bonus = entry.get("bonus_skill")
        if bonus:
            self._apply_bonus(bonus)
        return entry.get("title")

    def _apply_bonus(self, bonus: str) -> None:
        """Apply a rank bonus. '<Name> +<N>' against a known characteristic bumps it; otherwise add as a skill."""
        if not try_apply_characteristic_bonus(self.character, bonus):
            self.character.add_skill(bonus)


class ChooseCareerStep(Step):
    """Present available careers for the player to choose from."""

    step_id = "choose_career"
    step_type = StepType.CHOICE

    def __init__(self, character: Character, careers: list[dict]) -> None:
        super().__init__(character)
        self.careers = careers

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
            description="Choose a career to pursue.",
            options=[c["name"] for c in self.careers],
            required_count=1,
            data={"careers": self.careers},
        )

    def resolve(self, player_input: dict | None = None) -> None:
        if player_input is None:
            raise ValueError("Career selection is required.")
        selections = player_input.get("selections", [])
        if len(selections) != 1:
            raise ValueError("Must choose a single career.")
        self._selected_career_pending: str = selections[0]

    def apply(self) -> None:
        career = self._selected_career_pending
        self.outcome = StepOutcome(
            status="SELECTED",
            description=f"Pursuing career: {career}.",
            data={"career": career},
        )


class ContinueOrMusterOutStep(Step):
    """Ask whether to continue serving or muster out."""

    step_id = "continue_or_muster_out"
    step_type = StepType.CHOICE

    CONTINUE = "Continue"
    MUSTER_OUT = "Muster Out"

    def __init__(self, character: Character, career_name: str) -> None:
        super().__init__(character)
        self.career_name = career_name

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
                f"Your term in the {self.career_name} is complete. "
                "Continue serving or muster out?"
            ),
            options=[self.CONTINUE, self.MUSTER_OUT],
            required_count=1,
        )

    def resolve(self, player_input: dict | None = None) -> None:
        if player_input is None:
            raise ValueError("Decision is required.")
        selections = player_input.get("selections", [])
        if len(selections) != 1:
            raise ValueError("Must choose one option.")
        self._decision_pending: str = selections[0]

    def apply(self) -> None:
        decision = self._decision_pending
        status = "CONTINUE" if decision == self.CONTINUE else "MUSTER_OUT"
        self.outcome = StepOutcome(
            status=status,
            description=f"Decision: {decision}.",
            data={"decision": decision, "career_name": self.career_name},
        )


class TransitionTerm(Term):
    """A term containing a single decision step (career choice or muster out)."""

    def __init__(self, character: Character, step: Step) -> None:
        super().__init__(character)
        self.steps = [step]

    def label(self) -> str:
        inner = self.steps[0]
        if inner.step_id == ChooseCareerStep.step_id:
            return "Career Selection"
        if inner.step_id == ContinueOrMusterOutStep.step_id:
            # ContinueOrMusterOutStep carries career_name as an attribute.
            return f"{inner.career_name} — Term End"  # type: ignore[attr-defined]
        return "Transition"

    def next_term(self, session: "GameSession") -> "Term | None":
        # Local imports to avoid circular references.
        from src.career_loader import (
            career_to_term_kwargs,
            get_available_careers,
            load_career,
        )

        inner = self.steps[0]
        outcome = inner.outcome
        if outcome is None:
            return None

        if inner.step_id == ChooseCareerStep.step_id:
            career_name = outcome.data["career"]
            session.current_career_data = load_career(career_name)
            session.career_term_count = 0
            kwargs = career_to_term_kwargs(
                session.current_career_data, is_first_term=True
            )
            return CareerTerm(
                session.character,
                term_number=session.career_term_count + 1,
                **kwargs,
            )

        if inner.step_id == ContinueOrMusterOutStep.step_id:
            if outcome.status == "CONTINUE":
                kwargs = career_to_term_kwargs(
                    session.current_career_data, is_first_term=False
                )
                return CareerTerm(
                    session.character,
                    term_number=session.career_term_count + 1,
                    **kwargs,
                )
            # MUSTER_OUT — creation is done.
            return None

        return None


class CareerTerm(Term):
    """Live through a full career term.

    The progression is dynamic based on results and choices:
    1. First term: Qualify → Basic Training → Choose Assignment
       (If qualification fails, the term ends immediately. No skill roll on
       the first term — basic training is the only skill grant.)
    2. Subsequent terms: Choose Assignment → Choose Skill Table → Roll for Skill
    """

    def __init__(
        self,
        character: Character,
        career_name: str,
        qualification_characteristic: str,
        qualification_target: int,
        service_skills: list[str],
        assignments: list[dict],
        skill_tables: dict[str, list[str]],
        events: dict | None = None,
        mishaps: dict | None = None,
        ranks: list[dict] | None = None,
        is_first_term: bool = True,
        term_number: int = 1,
    ) -> None:
        super().__init__(character)
        self.career_name = career_name
        self.service_skills = service_skills
        self.assignments = assignments
        self.skill_tables = skill_tables
        self.events = events or {}
        self.mishaps = mishaps or {}
        self.ranks = ranks or []
        self.is_first_term = is_first_term
        self.term_number = term_number
        self._selected_assignment: dict | None = None

        if is_first_term:
            self.steps = [
                RollQualificationStep(
                    character, qualification_characteristic, qualification_target
                )
            ]
        else:
            self.steps = [ChooseAssignmentStep(character, assignments)]

    def label(self) -> str:
        return f"{self.career_name} — Term {self.term_number}"

    def advance(self) -> None:
        """Complete the current step and dynamically append the next steps based on outcomes."""
        step = self.current_step
        super().advance()

        if step is None or step.outcome is None:
            return

        status = step.outcome.status

        if isinstance(step, RollQualificationStep):
            if status == "QUALIFIED":
                self.steps.append(
                    BasicTrainingStep(self.character, self.service_skills)
                )
                self.steps.append(
                    ChooseAssignmentStep(self.character, self.assignments)
                )
            else:
                # Failed qualification ends the term immediately.
                self.outcome = StepOutcome(
                    status="FAILED_QUAL",
                    description="Qualification failed — returning to career selection.",
                )

        elif isinstance(step, ChooseAssignmentStep):
            self._selected_assignment = step.outcome.data["assignment"]
            if self.is_first_term:
                self.steps.append(
                    SurvivalCheckStep(self.character, self._selected_assignment)
                )
            else:
                self.steps.append(
                    ChooseCareerSkillsTable(
                        self.character, list(self.skill_tables.keys())
                    )
                )

        elif isinstance(step, ChooseCareerSkillsTable):
            skill_options = self.skill_tables[step.outcome.data["skill_table"]]
            self.steps.append(RollForSkillStep(self.character, skill_options))

        elif isinstance(step, RollForSkillStep):
            self.steps.append(
                SurvivalCheckStep(self.character, self._selected_assignment)
            )

        elif isinstance(step, SurvivalCheckStep):
            if status == "SURVIVED":
                self.steps.append(EventsRollStep(self.character, self.events))
                self.steps.append(
                    AdvancementRollStep(
                        self.character,
                        self.career_name,
                        self._selected_assignment,
                        self.ranks,
                    )
                )
            else:
                self.steps.append(MishapRollStep(self.character, self.mishaps))

        elif isinstance(step, MishapRollStep):
            self.outcome = StepOutcome(
                status="MISHAP",
                description="Career ended by mishap.",
            )

        elif isinstance(step, AdvancementRollStep):
            # End of a normal term. No more steps.
            self.outcome = StepOutcome(
                status="COMPLETED",
                description="Term completed.",
            )

    def next_term(self, session: "GameSession") -> "Term | None":
        from src.career_loader import (
            career_to_term_kwargs,
            get_available_careers,
        )

        status = self.outcome.status if self.outcome else None

        if status == "FAILED_QUAL":
            careers = get_available_careers()
            return TransitionTerm(
                session.character, ChooseCareerStep(session.character, careers)
            )

        if status == "MISHAP":
            session.current_career_data = None
            session.career_term_count = 0
            careers = get_available_careers()
            return TransitionTerm(
                session.character, ChooseCareerStep(session.character, careers)
            )

        if status == "COMPLETED":
            session.career_term_count += 1
            return TransitionTerm(
                session.character,
                ContinueOrMusterOutStep(session.character, self.career_name),
            )

        return None
