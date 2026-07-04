from __future__ import annotations

from src.career_data import Assignment
from src.character import Character
from src.terms.anagathics import (
    ANAGATHICS_SOC_TARGET,
    attempt_start_anagathics,
    maintain_anagathics,
)
from src.terms.base import (
    PassFailRollStep,
    SingleChoiceStep,
    Step,
    StepOutcome,
    StepPrompt,
    StepStatus,
    StepType,
)
from src.terms.careers.parsers import (
    apply_rank_bonus,
    parse_skill_entry,
    try_apply_characteristic_bonus,
)
from src.terms.effects import (
    apply_effects,
    has_effect,
    parse_entry as parse_effect_entry,
)
from src.utilities import roll


class RollQualificationStep(PassFailRollStep):
    """Roll 2d6 + DM to see if you qualify for the career."""

    step_id = "roll_qualification"
    check_label = "Qualification"
    status_pass = StepStatus.QUALIFIED
    status_fail = StepStatus.FAILED


class AutoQualifyStep(Step):
    """Automatic qualification for careers that gate entry on a characteristic minimum.

    Used by careers whose qualification YAML sets `auto: true` (e.g. Noble).
    Eligible characters reach this step only if their characteristic meets
    the threshold (career selection filters the rest out), so qualification
    always succeeds here.
    """

    step_id = "auto_qualify"
    step_type = StepType.AUTOMATIC

    def __init__(
        self,
        character: Character,
        characteristic: str,
        target: int,
    ) -> None:
        super().__init__(character=character)
        self.characteristic = characteristic
        self.target = target

    def apply(self) -> None:
        self.outcome = StepOutcome(
            status=StepStatus.QUALIFIED,
            description=(
                f"Automatically qualified ({self.characteristic} "
                f">= {self.target})."
            ),
            data={"characteristic": self.characteristic, "target": self.target},
        )

    def prompt(self) -> StepPrompt:
        if self.outcome is not None:
            description = self.outcome.description
        else:
            description = (
                f"Automatic qualification on {self.characteristic} "
                f">= {self.target}."
            )
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description=description,
        )


class BasicTrainingStep(Step):
    step_id = "basic_training"
    step_type = StepType.AUTOMATIC

    def __init__(self, character: Character, service_skills: list[str]):
        super().__init__(character=character)
        self.service_skills = service_skills

    def apply(self) -> None:
        for skill in self.service_skills:
            self.character.grant_skill(skill, level=0)
        self.outcome = StepOutcome(
            status=StepStatus.TRAINED,
            description=(
                f"Gained basic training skills: {', '.join(self.service_skills)}."
            ),
            data={"service_skills": list(self.service_skills)},
        )

    def prompt(self) -> StepPrompt:
        if self.outcome is not None:
            description = self.outcome.description
        else:
            description = (
                "Basic training: gain every Service Skill at level 0 "
                f"({', '.join(self.service_skills)})."
            )
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description=description,
        )


class PickServiceSkillStep(SingleChoiceStep):
    """Subsequent-career basic training: pick one Service Skill at level 0."""

    step_id = "pick_service_skill"
    input_required_message = "Service-skill selection is required."
    single_choice_message = "Must choose a single service skill."

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
            options=self.options(),
            required_count=1,
        )

    def options(self) -> list[str]:
        return list(self.service_skills)

    def invalid_choice_message(self, selection: str) -> str:
        return f"Unknown service skill: {selection}"

    def on_choice(self, selection: str) -> None:
        self._selected_skill_pending = selection

    def apply(self) -> None:
        skill = self._selected_skill_pending
        self.character.grant_skill(skill, level=0)
        self.outcome = StepOutcome(
            status=StepStatus.TRAINED,
            description=f"Gained {skill} at level 0 (subsequent-career basic training).",
            data={"service_skill": skill},
        )


class ChooseAssignmentStep(SingleChoiceStep):
    """Choose an assignment under the given career."""

    step_id = "choose_assignment"
    input_required_message = "Assignment selection is required."
    single_choice_message = "Must choose a single assignment"

    def __init__(self, character: Character, assignments: list[Assignment]):
        super().__init__(character=character)
        self.assignments = assignments
        # Set in apply(): the chosen typed Assignment, read by the owning
        # term's transition handler. The dict form lives in outcome.data
        # only for the API/frontend.
        self.selected_assignment: Assignment | None = None

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
            options=self.options(),
            required_count=1,
        )

    def options(self) -> list[str]:
        return [a.name for a in self.assignments]

    def invalid_choice_message(self, selection: str) -> str:
        return f"Unknown assignment: {selection}"

    def on_choice(self, selection: str) -> None:
        matching = [a for a in self.assignments if a.name == selection]
        self._selected_assignment_pending: Assignment = matching[0]

    def apply(self) -> None:
        assignment = self._selected_assignment_pending
        self.selected_assignment = assignment
        self.outcome = StepOutcome(
            status=StepStatus.SELECTED,
            description=f"Assignment: {assignment.name}.",
            data={"assignment": assignment.model_dump(), "name": assignment.name},
        )


class ChooseCareerSkillsTable(SingleChoiceStep):
    """Choose which skill table to roll on.

    Tables may declare a per-table requirement (e.g. EDU 8+ to access the
    Advanced Education table); only tables the character currently meets
    are offered as options.
    """

    step_id = "choose_career_skills_table"
    input_required_message = "Skill table selection is required."
    single_choice_message = "Must choose a single skill table."

    def __init__(
        self,
        character: Character,
        skill_tables: list[str],
        requirements: dict[str, dict] | None = None,
        career_name: str | None = None,
    ):
        super().__init__(character=character)
        self.skill_tables = skill_tables
        self.requirements = requirements or {}
        self.career_name = career_name

    def _meets_requirement(self, table_name: str) -> bool:
        req = self.requirements.get(table_name)
        if not req:
            return True
        # Commission gate: table is only available to officers of this career.
        if req.get("commissioned"):
            if self.career_name is None:
                return False
            record = self.character.careers.get(self.career_name)
            if record is None or not record.commissioned:
                return False
        characteristic = req.get("characteristic")
        minimum = req.get("minimum")
        if characteristic is not None and minimum is not None:
            stat = self.character.characteristics.get(characteristic)
            if stat is None:
                return False
            if stat.value < minimum:
                return False
        return True

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
            options=self.options(),
            required_count=1,
        )

    def options(self) -> list[str]:
        return self.available_tables()

    def invalid_choice_message(self, selection: str) -> str:
        return f"You do not meet the requirements for the {selection} skill table."

    def on_choice(self, selection: str) -> None:
        self._selected_skill_table_pending = selection

    def apply(self) -> None:
        table = self._selected_skill_table_pending
        self.outcome = StepOutcome(
            status=StepStatus.SELECTED,
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
            status=StepStatus.ROLLED,
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
    status_pass = StepStatus.SURVIVED
    status_fail = StepStatus.FAILED

    def __init__(self, character: Character, assignment: Assignment) -> None:
        survival = assignment.survival
        super().__init__(
            character=character,
            check_characteristic=survival.characteristic,
            target=survival.target,
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
    """Roll d6 on the career's mishap table and apply any structured effects.

    YAML entries may be plain strings (flavor only) or `{text, effects}`
    dicts; see `src.terms.effects` for the effect vocabulary.
    """

    step_id = "mishap_roll"
    step_type = StepType.AUTOMATIC

    def __init__(self, character: Character, mishaps: dict) -> None:
        super().__init__(character=character)
        self.mishaps = mishaps

    def resolve(self, player_input: dict | None = None) -> None:
        self.mishap_roll: int = roll(1)
        entry = self.mishaps.get(self.mishap_roll, "")
        self.mishap_text, self._effects = parse_effect_entry(entry)

    def apply(self) -> None:
        applied = apply_effects(self.character, self._effects)
        detail = ""
        if applied:
            detail = " Effects: " + "; ".join(applied) + "."
        self.outcome = StepOutcome(
            status=StepStatus.MISHAP,
            description=(
                f"Mishap! Rolled {self.mishap_roll}: {self.mishap_text} "
                f"Your career ends.{detail}"
            ),
            data={
                "roll": self.mishap_roll,
                "text": self.mishap_text,
                "effects_applied": applied,
            },
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
    """Roll 2d6 on the career's events table and apply any structured effects.

    YAML entries may be plain strings (flavor only) or `{text, effects}`
    dicts; see `src.terms.effects` for the effect vocabulary. A
    `forced_exit` effect surfaces as `self.forced_exit=True` so the
    owning `CareerTerm` can end the term with FORCED_EXIT status.
    """

    step_id = "events_roll"
    step_type = StepType.AUTOMATIC

    def __init__(self, character: Character, events: dict) -> None:
        super().__init__(character=character)
        self.events = events
        self.forced_exit: bool = False

    def resolve(self, player_input: dict | None = None) -> None:
        self.event_roll: int = roll(2)
        entry = self.events.get(self.event_roll, "")
        self.event_text, self._effects = parse_effect_entry(entry)

    def apply(self) -> None:
        applied = apply_effects(self.character, self._effects)
        self.forced_exit = has_effect(self._effects, "forced_exit")
        detail = ""
        if applied:
            detail = " Effects: " + "; ".join(applied) + "."
        self.outcome = StepOutcome(
            status=StepStatus.EVENT,
            description=(
                f"Event (2d6 = {self.event_roll}): {self.event_text}{detail}"
            ),
            data={
                "roll": self.event_roll,
                "text": self.event_text,
                "effects_applied": applied,
                "forced_exit": self.forced_exit,
            },
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
    status_pass = StepStatus.PROMOTED
    status_fail = StepStatus.NOT_PROMOTED
    status_at_max_rank = StepStatus.AT_MAX_RANK

    def __init__(
        self,
        character: Character,
        career_name: str,
        assignment: Assignment,
        ranks: list[dict],
        officer_ranks: list[dict] | None = None,
    ) -> None:
        advancement = assignment.advancement
        super().__init__(
            character=character,
            check_characteristic=advancement.characteristic,
            target=advancement.target,
        )
        self.career_name = career_name
        self.assignment = assignment
        self.enlisted_ranks = ranks
        self.officer_ranks = officer_ranks or []
        # Pick enlisted vs officer rank track at apply-time from the
        # character's commissioned flag for this career.
        record = character.careers.get(career_name)
        self.ranks = (
            self.officer_ranks
            if (record is not None and record.commissioned and self.officer_ranks)
            else self.enlisted_ranks
        )
        self.max_rank: int | None = (
            max(r["rank"] for r in self.ranks) if self.ranks else None
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
            outcome_str = status.value
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
        """Apply the promoted rank's bonus skill/characteristic; return its title."""
        return apply_rank_bonus(self.character, self.ranks, new_rank)


class CommissionStep(SingleChoiceStep):
    """Optional commission attempt for military careers.

    Player first chooses Attempt or Skip. On Attempt, roll 2d6 + DM vs the
    commission target. Success makes the character a rank 1 officer and
    replaces the advancement roll for this term (so `terms_served` is
    ticked here).

    Eligibility is decided at append-time by `CareerTerm`: first term,
    or SOC >= 9 in any term (with DM -1 per term after the first).
    """

    step_id = "commission"
    input_required_message = "Commission decision is required."
    single_choice_message = "Must choose a single commission option."

    ATTEMPT = "Attempt"
    SKIP = "Skip"

    def __init__(
        self,
        character: Character,
        career_name: str,
        characteristic: str,
        target: int,
        dm: int,
        officer_ranks: list[dict],
    ) -> None:
        super().__init__(character=character)
        self.career_name = career_name
        self.characteristic = characteristic
        self.target = target
        self.dm = dm
        self.officer_ranks = officer_ranks
        self._decision_pending: str | None = None
        self.raw_roll: int | None = None
        self.total_roll: int | None = None

    def _total_dm(self) -> int:
        stat = self.character.characteristics.get(self.characteristic)
        stat_mod = stat.modifier() if stat is not None else 0
        return stat_mod + self.dm

    def prompt(self) -> StepPrompt:
        if self.outcome is not None:
            return StepPrompt(
                step_id=self.step_id,
                step_type=self.step_type,
                description=self.outcome.description,
            )
        total_dm = self._total_dm()
        sign = "+" if total_dm >= 0 else ""
        description = (
            f"You may attempt a commission. Roll 2d6 {sign}{total_dm} "
            f"on {self.characteristic} vs {self.target}. "
            "On success you become a rank 1 officer and skip this term's "
            "advancement roll."
        )
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description=description,
            options=self.options(),
            required_count=1,
        )

    def options(self) -> list[str]:
        return [self.ATTEMPT, self.SKIP]

    def invalid_choice_message(self, selection: str) -> str:
        return f"Unknown commission option: {selection}"

    def on_choice(self, selection: str) -> None:
        self._decision_pending = selection
        if selection == self.ATTEMPT:
            self.raw_roll = roll(2)
            self.total_roll = self.raw_roll + self._total_dm()

    def apply(self) -> None:
        if self._decision_pending == self.SKIP:
            self.outcome = StepOutcome(
                status=StepStatus.SKIPPED,
                description="Declined to attempt a commission this term.",
                data={"decision": "skip"},
            )
            return

        assert self.total_roll is not None and self.raw_roll is not None
        if self.total_roll >= self.target:
            record = self.character.ensure_career(self.career_name)
            record.commissioned = True
            record.rank = 1
            new_rank_title = self._apply_officer_rank_bonus(1)
            # Commission replaces advancement this term — tick terms_served
            # here so the count is correct when the term ends.
            self.character.record_career_term(self.career_name)
            self.outcome = StepOutcome(
                status=StepStatus.COMMISSIONED,
                description=(
                    f"Commission check on {self.characteristic}: rolled "
                    f"{self.total_roll} vs target {self.target} — COMMISSIONED"
                    + (f" as {new_rank_title}." if new_rank_title else ".")
                ),
                data={
                    "raw_roll": self.raw_roll,
                    "total_roll": self.total_roll,
                    "target": self.target,
                    "new_rank_title": new_rank_title,
                },
            )
        else:
            self.outcome = StepOutcome(
                status=StepStatus.FAILED_COMMISSION,
                description=(
                    f"Commission check on {self.characteristic}: rolled "
                    f"{self.total_roll} vs target {self.target} — FAILED."
                ),
                data={
                    "raw_roll": self.raw_roll,
                    "total_roll": self.total_roll,
                    "target": self.target,
                },
            )

    def _apply_officer_rank_bonus(self, new_rank: int) -> str | None:
        return apply_rank_bonus(self.character, self.officer_ranks, new_rank)


class ChooseCareerStep(SingleChoiceStep):
    """Present available careers for the player to choose from."""

    step_id = "choose_career"
    input_required_message = "Career selection is required."
    single_choice_message = "Must choose a single career."

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
            options=self.options(),
            required_count=1,
            data={"careers": self.careers},
        )

    def options(self) -> list[str]:
        return [c["name"] for c in self.careers]

    def invalid_choice_message(self, selection: str) -> str:
        return f"Unknown career: {selection}"

    def on_choice(self, selection: str) -> None:
        self._selected_career_pending = selection

    def apply(self) -> None:
        career = self._selected_career_pending
        self.outcome = StepOutcome(
            status=StepStatus.SELECTED,
            description=f"Pursuing career: {career}.",
            data={"career": career},
        )


class ContinueOrMusterOutStep(SingleChoiceStep):
    """Ask whether to continue serving, muster out, or change assignment."""

    step_id = "continue_or_muster_out"
    input_required_message = "Decision is required."
    single_choice_message = "Must choose one option."

    CONTINUE = "Continue"
    MUSTER_OUT = "Muster Out"
    CHANGE_ASSIGNMENT = "Change Assignment"

    def __init__(
        self,
        character: Character,
        career_name: str,
        assignment_change_group: str | None = None,
        current_assignment: Assignment | None = None,
        assignments: list[Assignment] | None = None,
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
            if a.name != self.current_assignment.name
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
            options=self.options(),
            required_count=1,
        )

    def options(self) -> list[str]:
        return self._options()

    def on_choice(self, selection: str) -> None:
        self._decision_pending = selection

    def apply(self) -> None:
        decision = self._decision_pending
        status = {
            self.CONTINUE: StepStatus.CONTINUE,
            self.MUSTER_OUT: StepStatus.MUSTER_OUT,
            self.CHANGE_ASSIGNMENT: StepStatus.CHANGE_ASSIGNMENT,
        }[decision]
        self.outcome = StepOutcome(
            status=status,
            description=f"Decision: {decision}.",
            data={"decision": decision, "career_name": self.career_name},
        )


class MusterOutOrNewCareerStep(SingleChoiceStep):
    """Offered after a mishap: muster out with benefits or choose a new career."""

    step_id = "muster_out_or_new_career"
    input_required_message = "Decision is required."
    single_choice_message = "Must choose one option."

    MUSTER_OUT = "Muster Out"
    CHOOSE_CAREER = "Choose New Career"

    def __init__(self, character: Character, career_name: str) -> None:
        super().__init__(character)
        self.career_name = career_name

    def _options(self) -> list[str]:
        return [self.MUSTER_OUT, self.CHOOSE_CAREER]

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
                f"Your career in the {self.career_name} ended after a mishap. "
                "Muster out with benefits for terms served, or choose a new career?"
            ),
            options=self.options(),
            required_count=1,
        )

    def options(self) -> list[str]:
        return self._options()

    def on_choice(self, selection: str) -> None:
        self._decision_pending = selection

    def apply(self) -> None:
        decision = self._decision_pending
        status = {
            self.MUSTER_OUT: StepStatus.MUSTER_OUT,
            self.CHOOSE_CAREER: StepStatus.CHOOSE_CAREER,
        }[decision]
        self.outcome = StepOutcome(
            status=status,
            description=f"Decision: {decision}.",
            data={"decision": decision, "career_name": self.career_name},
        )


class ChooseDraftOrDrifterStep(SingleChoiceStep):
    """Offered after a failed qualification: Draft (once per life) or Drifter.

    Draft rolls 1d6 to assign the character to a random service. Drifter
    is always available. Chosen career is entered next with automatic
    qualification (first term).
    """

    step_id = "choose_draft_or_drifter"
    input_required_message = "Draft-or-Drifter decision is required."
    single_choice_message = "Must choose one option."

    DRAFT = "Draft"
    DRIFTER = "Drifter"

    # 1d6 draft table per the rules.
    DRAFT_TABLE: dict[int, str] = {
        1: "Navy",
        2: "Army",
        3: "Marine",
        4: "Merchant",
        5: "Scout",
        6: "Agent",
    }

    def __init__(self, character: Character, draft_used: bool) -> None:
        super().__init__(character)
        self.draft_used = draft_used
        self._decision_pending: str | None = None
        self.draft_roll: int | None = None
        self.assigned_career: str | None = None

    def _options(self) -> list[str]:
        options = []
        if not self.draft_used:
            options.append(self.DRAFT)
        options.append(self.DRIFTER)
        return options

    def prompt(self) -> StepPrompt:
        if self.outcome is not None:
            return StepPrompt(
                step_id=self.step_id,
                step_type=self.step_type,
                description=self.outcome.description,
            )
        if self.draft_used:
            description = (
                "Qualification failed. The Draft has already been used — "
                "your only remaining fallback is the Drifter career."
            )
        else:
            description = (
                "Qualification failed. You may enter the Draft (roll 1d6 for "
                "a random service assignment, once per life) or fall back on "
                "the Drifter career."
            )
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description=description,
            options=self.options(),
            required_count=1,
        )

    def options(self) -> list[str]:
        return self._options()

    def on_choice(self, selection: str) -> None:
        self._decision_pending = selection
        if selection == self.DRAFT:
            self.draft_roll = roll(1)
            self.assigned_career = self.DRAFT_TABLE.get(self.draft_roll)

    def apply(self) -> None:
        if self._decision_pending == self.DRIFTER:
            self.assigned_career = "Drifter"
            self.outcome = StepOutcome(
                status=StepStatus.DRIFTER,
                description="Fell back to the Drifter career.",
                data={"career": "Drifter"},
            )
            return
        assert self.draft_roll is not None and self.assigned_career is not None
        self.outcome = StepOutcome(
            status=StepStatus.DRAFTED,
            description=(
                f"Drafted — rolled {self.draft_roll} on the Draft table: "
                f"assigned to the {self.assigned_career} career."
            ),
            data={
                "career": self.assigned_career,
                "roll": self.draft_roll,
            },
        )


class ChooseAnagathicsStep(SingleChoiceStep):
    """Offer the optional anagathics rule at the start of a career term.

    Only shown when the anagathics rule is enabled and no course is active
    yet. The player may attempt to start a course (roll SOC 10+) or decline.
    A natural 2 on the acquisition roll routes the Traveller straight to the
    Prisoner career this term (surfaced as ``ANAGATHICS_PRISONER`` for the
    term to branch on); a success starts the course and charges its first
    term's 1D×Cr25000 cost.
    """

    step_id = "choose_anagathics"
    input_required_message = "Anagathics decision is required."
    single_choice_message = "Must choose one option."

    START = "Start anagathics"
    DECLINE = "Do not take anagathics"

    def __init__(self, character: Character) -> None:
        super().__init__(character)
        self._decision_pending: str | None = None

    def _options(self) -> list[str]:
        return [self.START, self.DECLINE]

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
                "Start a course of anagathics (anti-aging drugs)? Requires a "
                f"Social Standing {ANAGATHICS_SOC_TARGET}+ roll, costs "
                "1D×Cr25000 per term (may go into debt), and forces two "
                "Survival checks each term. A natural 2 sends you straight to "
                "the Prisoner career."
            ),
            options=self.options(),
            required_count=1,
        )

    def options(self) -> list[str]:
        return self._options()

    def on_choice(self, selection: str) -> None:
        self._decision_pending = selection

    def apply(self) -> None:
        if self._decision_pending == self.DECLINE:
            self.outcome = StepOutcome(
                status=StepStatus.ANAGATHICS_DECLINED,
                description="Declined anagathics this term.",
            )
            return
        result = attempt_start_anagathics(self.character)
        if result.to_prisoner:
            self.outcome = StepOutcome(
                status=StepStatus.ANAGATHICS_PRISONER,
                description=(
                    "A botched anagathics dose (natural 2) — sent straight to "
                    "the Prisoner career this term."
                ),
                data={"rolled": result.rolled, "total": result.total},
            )
        elif result.started:
            self.outcome = StepOutcome(
                status=StepStatus.ANAGATHICS_STARTED,
                description=(
                    f"Started anagathics — rolled {result.total} vs "
                    f"{ANAGATHICS_SOC_TARGET}. This term's course costs "
                    f"Cr{result.cost}."
                ),
                data={
                    "rolled": result.rolled,
                    "soc_dm": result.soc_dm,
                    "total": result.total,
                    "cost": result.cost,
                },
            )
        else:
            self.outcome = StepOutcome(
                status=StepStatus.ANAGATHICS_MISSED,
                description=(
                    f"Failed to obtain anagathics — rolled {result.total} vs "
                    f"{ANAGATHICS_SOC_TARGET}."
                ),
                data={
                    "rolled": result.rolled,
                    "soc_dm": result.soc_dm,
                    "total": result.total,
                },
            )


class AnagathicsUpkeepStep(Step):
    """Charge the per-term maintenance for an already-active course.

    Automatic step run at the start of a career term when a course is active:
    rolls this term's 1D×Cr25000 cost, extends the course (raising its Ageing
    DM), and reports the charge. Survival is doubled elsewhere in the term.
    """

    step_id = "anagathics_upkeep"
    step_type = StepType.AUTOMATIC

    def __init__(self, character: Character) -> None:
        super().__init__(character)
        self._cost: int = 0

    def resolve(self, player_input: dict | None = None) -> None:
        self._cost = maintain_anagathics(self.character)

    def apply(self) -> None:
        course = self.character.anagathics
        terms_used = course.terms_used if course is not None else 0
        self.outcome = StepOutcome(
            status=StepStatus.ANAGATHICS_MAINTAINED,
            description=(
                f"Maintained anagathics (term {terms_used}) — cost Cr{self._cost}."
            ),
            data={"cost": self._cost, "terms_used": terms_used},
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
            description="Paying this term's anagathics upkeep (1D×Cr25000).",
        )
