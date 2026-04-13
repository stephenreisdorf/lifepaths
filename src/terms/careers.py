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


def parse_skill_entry(entry: str) -> tuple[str, str | None, int | None]:
    """Parse a skill-table entry into (name, specialty, level).

    Forms handled:
      - "Skill"                → (name, None, None)  bare: +1, or grant at 1
      - "Skill 0"              → (name, None, 0)     ensure exists at 0
      - "Skill N"              → (name, None, N)     raise to N
      - "Parent (Specialty)"   → (parent, specialty, None)
      - "Parent (Specialty) N" → (parent, specialty, N)
    """
    entry = entry.strip()
    level: int | None = None
    tokens = entry.rsplit(" ", 1)
    if len(tokens) == 2 and tokens[1].lstrip("-").isdigit():
        entry, level = tokens[0].rstrip(), int(tokens[1])

    specialty: str | None = None
    if entry.endswith(")") and "(" in entry:
        paren = entry.rfind("(")
        specialty = entry[paren + 1 : -1].strip()
        entry = entry[:paren].rstrip()

    return entry, specialty, level


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


class PickServiceSkillStep(Step):
    """Subsequent-career basic training: pick one Service Skill at level 0."""

    step_id = "pick_service_skill"
    step_type = StepType.CHOICE

    def __init__(self, character: Character, service_skills: list[str]):
        super().__init__(character=character)
        self.service_skills = service_skills

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
                "Subsequent-career basic training: pick one Service Skill "
                "at level 0."
            ),
            options=list(self.service_skills),
            required_count=1,
        )

    def resolve(self, player_input: dict | None = None) -> None:
        if player_input is None:
            raise ValueError("Service-skill selection is required.")
        selections = player_input.get("selections", [])
        if len(selections) != 1:
            raise ValueError("Must choose a single service skill.")
        chosen = selections[0]
        if chosen not in self.service_skills:
            raise ValueError(f"Unknown service skill: {chosen}")
        self._selected_skill_pending: str = chosen

    def apply(self) -> None:
        skill = self._selected_skill_pending
        self.character.add_skill(skill)
        self.outcome = StepOutcome(
            status="TRAINED",
            description=f"Gained {skill} at level 0 (subsequent-career basic training).",
            data={"service_skill": skill},
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
    """Choose which skill table to roll on.

    Tables may declare a per-table requirement (e.g. EDU 8+ to access the
    Advanced Education table); only tables the character currently meets
    are offered as options.
    """

    step_id = "choose_career_skills_table"
    step_type = StepType.CHOICE

    def __init__(
        self,
        character: Character,
        skill_tables: list[str],
        requirements: dict[str, dict] | None = None,
    ):
        super().__init__(character=character)
        self.skill_tables = skill_tables
        self.requirements = requirements or {}

    def _meets_requirement(self, table_name: str) -> bool:
        req = self.requirements.get(table_name)
        if not req:
            return True
        characteristic = req.get("characteristic")
        minimum = req.get("minimum")
        if characteristic is None or minimum is None:
            return True
        stat = self.character.characteristics.get(characteristic)
        if stat is None:
            return False
        return stat.value >= minimum

    def available_tables(self) -> list[str]:
        return [t for t in self.skill_tables if self._meets_requirement(t)]

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
            options=self.available_tables(),
            required_count=1,
        )

    def resolve(self, player_input: dict | None = None) -> None:
        if player_input is None:
            raise ValueError("Skill table selection is required.")
        selections = player_input.get("selections", [])
        if len(selections) != 1:
            raise ValueError("Must choose a single skill table.")
        chosen = selections[0]
        if not self._meets_requirement(chosen):
            raise ValueError(
                f"You do not meet the requirements for the {chosen} skill table."
            )
        self._selected_skill_table_pending: str = chosen

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
            name, specialty, level = parse_skill_entry(self.skill)
            self.character.grant_skill(name, level=level, specialty=specialty)
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
        record = self.character.record_career_term(self.career_name)
        terms_after = record.terms_served

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
                promoted = self.character.promote(self.career_name)
                status = self.status_pass
                self.new_rank_title = self._apply_rank_bonus(promoted.rank)
        else:
            status = self.status_fail
            self.new_rank_title = None

        # Natural 12 forces the character to stay (overrides forced-exit);
        # otherwise, a modified roll ≤ terms served forces them out.
        self.forced_stay: bool = self.raw_roll == 12
        self.forced_exit: bool = (
            not self.forced_stay and self.total_roll <= terms_after
        )
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
                "forced_stay": self.forced_stay,
                "forced_exit": self.forced_exit,
                "terms_served": terms_after,
            },
        )

    def _post_description(self, status: str) -> str:
        if status == self.status_pass and self.new_rank_title:
            outcome_str = f"PROMOTED to {self.new_rank_title}"
        elif status == self.status_at_max_rank:
            outcome_str = "already at top rank — no promotion"
        else:
            outcome_str = status
        if self.raw_roll == 12:
            suffix = " (natural 12 — forced to stay)"
        elif getattr(self, "forced_exit", False):
            suffix = " (roll ≤ terms served — forced to leave)"
        else:
            suffix = ""
        return (
            f"Advancement check on {self.check_characteristic}: "
            f"rolled {self.total_roll} vs target {self.target} — "
            f"{outcome_str}{suffix}."
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
    """Ask whether to continue serving, muster out, or change assignment."""

    step_id = "continue_or_muster_out"
    step_type = StepType.CHOICE

    CONTINUE = "Continue"
    MUSTER_OUT = "Muster Out"
    CHANGE_ASSIGNMENT = "Change Assignment"

    def __init__(
        self,
        character: Character,
        career_name: str,
        assignment_change_group: str | None = None,
        current_assignment: dict | None = None,
        assignments: list[dict] | None = None,
    ) -> None:
        super().__init__(character)
        self.career_name = career_name
        self.assignment_change_group = assignment_change_group
        self.current_assignment = current_assignment
        self.assignments = assignments or []

    def _change_assignment_available(self) -> bool:
        # Rule: cannot change assignment if ejected from the career.
        record = self.character.careers.get(self.career_name)
        if record is not None and record.ejected:
            return False
        if self.assignment_change_group is None:
            return False
        if self.current_assignment is None:
            return False
        # Need at least one other assignment to switch to.
        others = [
            a for a in self.assignments
            if a["name"] != self.current_assignment["name"]
        ]
        return len(others) > 0

    def _options(self) -> list[str]:
        options = [self.CONTINUE, self.MUSTER_OUT]
        if self._change_assignment_available():
            options.append(self.CHANGE_ASSIGNMENT)
        return options

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
                "Continue serving, muster out, or change assignment?"
            ),
            options=self._options(),
            required_count=1,
        )

    def resolve(self, player_input: dict | None = None) -> None:
        if player_input is None:
            raise ValueError("Decision is required.")
        selections = player_input.get("selections", [])
        if len(selections) != 1:
            raise ValueError("Must choose one option.")
        decision = selections[0]
        if decision not in self._options():
            raise ValueError(f"Unavailable option: {decision}")
        self._decision_pending: str = decision

    def apply(self) -> None:
        decision = self._decision_pending
        status = {
            self.CONTINUE: "CONTINUE",
            self.MUSTER_OUT: "MUSTER_OUT",
            self.CHANGE_ASSIGNMENT: "CHANGE_ASSIGNMENT",
        }[decision]
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
            # Block only applies to the immediately-following selection;
            # once a new career is picked the block is lifted.
            session.blocked_career = None
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
            if outcome.status == "CHANGE_ASSIGNMENT":
                # Hand off to the assignment-change sub-term. It will
                # roll qualification for the new assignment and, on
                # success, start a new CareerTerm with rank reset to 0.
                data = session.current_career_data
                return AssignmentChangeTerm(
                    session.character,
                    career_name=data["name"],
                    assignments=data["assignments"],
                    current_assignment=session.current_assignment,
                    qualification_characteristic=data["qualification"]["characteristic"],
                    qualification_target=data["qualification"]["target"],
                )
            # MUSTER_OUT — creation is done.
            session.current_assignment = None
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
        skill_table_requirements: dict[str, dict] | None = None,
        events: dict | None = None,
        mishaps: dict | None = None,
        ranks: list[dict] | None = None,
        assignment_change_group: str | None = None,
        assignment_override: dict | None = None,
        is_first_term: bool = True,
        term_number: int = 1,
    ) -> None:
        super().__init__(character)
        self.career_name = career_name
        self.qualification_characteristic = qualification_characteristic
        self.qualification_target = qualification_target
        self.service_skills = service_skills
        self.assignments = assignments
        self.skill_tables = skill_tables
        self.skill_table_requirements = skill_table_requirements or {}
        self.events = events or {}
        self.mishaps = mishaps or {}
        self.ranks = ranks or []
        self.assignment_change_group = assignment_change_group
        self.is_first_term = is_first_term
        self.term_number = term_number
        self._selected_assignment: dict | None = None

        if is_first_term:
            self.steps = [
                RollQualificationStep(
                    character, qualification_characteristic, qualification_target
                )
            ]
        elif assignment_override is not None:
            # Continuing within the same career without re-prompting for
            # assignment (used by the assignment-change flow to carry
            # forward the chosen / retained assignment).
            self._selected_assignment = assignment_override
            self.steps = [
                ChooseCareerSkillsTable(
                    character,
                    list(self.skill_tables.keys()),
                    requirements=self.skill_table_requirements,
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
                # First career ever → full Basic Training at level 0.
                # Subsequent career → pick one Service Skill at level 0.
                if not self.character.careers:
                    self.steps.append(
                        BasicTrainingStep(self.character, self.service_skills)
                    )
                else:
                    self.steps.append(
                        PickServiceSkillStep(self.character, self.service_skills)
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
                        self.character,
                        list(self.skill_tables.keys()),
                        requirements=self.skill_table_requirements,
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
            self.character.mark_career_ejected(self.career_name)
            self.character.record_career_term(self.career_name)
            self.outcome = StepOutcome(
                status="MISHAP",
                description="Career ended by mishap.",
            )

        elif isinstance(step, AdvancementRollStep):
            # End of a normal term. Natural 12 overrides everything else
            # (forced stay). Otherwise a modified roll ≤ terms served
            # forces the character out of the career.
            if step.forced_stay:
                self.outcome = StepOutcome(
                    status="FORCED_STAY",
                    description="Natural 12 — forced to stay in the career.",
                )
            elif step.forced_exit:
                self.outcome = StepOutcome(
                    status="FORCED_EXIT",
                    description=(
                        "Advancement roll did not exceed terms served — "
                        "forced to leave the career."
                    ),
                )
            else:
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
            # A failed qualification doesn't lift an outstanding re-entry
            # block from an earlier mishap.
            careers = [
                c for c in get_available_careers()
                if c["name"] != session.blocked_career
            ]
            return TransitionTerm(
                session.character, ChooseCareerStep(session.character, careers)
            )

        if status == "MISHAP":
            session.current_career_data = None
            session.career_term_count = 0
            session.blocked_career = self.career_name
            session.current_assignment = None
            careers = [
                c for c in get_available_careers()
                if c["name"] != session.blocked_career
            ]
            return TransitionTerm(
                session.character, ChooseCareerStep(session.character, careers)
            )

        if status == "COMPLETED":
            session.career_term_count += 1
            session.current_assignment = self._selected_assignment
            return TransitionTerm(
                session.character,
                ContinueOrMusterOutStep(
                    session.character,
                    self.career_name,
                    assignment_change_group=self.assignment_change_group,
                    current_assignment=self._selected_assignment,
                    assignments=self.assignments,
                ),
            )

        if status == "FORCED_EXIT":
            # Forced out by advancement ≤ terms served. No Continue /
            # Muster choice — go straight to Career Selection. The
            # "cannot re-enter next term" rule applies to any leaving.
            session.current_career_data = None
            session.career_term_count = 0
            session.blocked_career = self.career_name
            session.current_assignment = None
            careers = [
                c for c in get_available_careers()
                if c["name"] != session.blocked_career
            ]
            return TransitionTerm(
                session.character, ChooseCareerStep(session.character, careers)
            )

        if status == "FORCED_STAY":
            # Natural 12 on advancement — skip continue/muster and start
            # the next term in the same career immediately.
            session.career_term_count += 1
            kwargs = career_to_term_kwargs(
                session.current_career_data, is_first_term=False
            )
            return CareerTerm(
                session.character,
                term_number=session.career_term_count + 1,
                **kwargs,
            )

        return None


class AssignmentChangeTerm(Term):
    """Handle the assignment-change flow.

    Pick a new assignment within the same career, then roll career
    qualification. On success, a fresh term begins at the new
    assignment with rank reset to 0 (per RAW). On failure, the
    character is forced out of the career entirely.
    """

    def __init__(
        self,
        character: Character,
        career_name: str,
        assignments: list[dict],
        current_assignment: dict,
        qualification_characteristic: str,
        qualification_target: int,
    ) -> None:
        super().__init__(character)
        self.career_name = career_name
        self.assignments = assignments
        self.current_assignment = current_assignment
        self.qualification_characteristic = qualification_characteristic
        self.qualification_target = qualification_target
        others = [
            a for a in assignments if a["name"] != current_assignment["name"]
        ]
        self.steps = [ChooseAssignmentStep(character, others)]
        self._chosen_assignment: dict | None = None

    def label(self) -> str:
        return f"{self.career_name} — Change Assignment"

    def advance(self) -> None:
        step = self.current_step
        super().advance()
        if step is None or step.outcome is None:
            return

        if isinstance(step, ChooseAssignmentStep):
            self._chosen_assignment = step.outcome.data["assignment"]
            self.steps.append(
                RollQualificationStep(
                    self.character,
                    self.qualification_characteristic,
                    self.qualification_target,
                )
            )
        elif isinstance(step, RollQualificationStep):
            if step.outcome.status == "QUALIFIED":
                self.outcome = StepOutcome(
                    status="CHANGED",
                    description=(
                        f"Qualified for {self._chosen_assignment['name']} — "
                        "career begins afresh at rank 0."
                    ),
                )
            else:
                self.outcome = StepOutcome(
                    status="CHANGE_FAILED",
                    description=(
                        "Failed to qualify for the new assignment — "
                        "forced out of the career."
                    ),
                )

    def next_term(self, session: "GameSession") -> "Term | None":
        from src.career_loader import (
            career_to_term_kwargs,
            get_available_careers,
        )

        status = self.outcome.status if self.outcome else None

        if status == "CHANGED":
            # RAW: rank resets to 0 when the assignment changes.
            record = self.character.ensure_career(self.career_name)
            record.rank = 0
            session.current_assignment = self._chosen_assignment
            kwargs = career_to_term_kwargs(
                session.current_career_data, is_first_term=False
            )
            return CareerTerm(
                session.character,
                term_number=session.career_term_count + 1,
                assignment_override=self._chosen_assignment,
                **kwargs,
            )

        if status == "CHANGE_FAILED":
            session.current_career_data = None
            session.career_term_count = 0
            session.blocked_career = self.career_name
            session.current_assignment = None
            careers = [
                c for c in get_available_careers()
                if c["name"] != session.blocked_career
            ]
            return TransitionTerm(
                session.character, ChooseCareerStep(session.character, careers)
            )

        return None
