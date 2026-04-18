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
from src.terms.effects import (
    apply_effects,
    has_effect,
    parse_entry as parse_effect_entry,
)
from src.utilities import roll


def _available_careers_for(character: Character, blocked: str | None) -> list[dict]:
    """Career list for ChooseCareerStep — filtered by eligibility and block."""
    from src.career_loader import filter_eligible_careers, get_available_careers

    careers = filter_eligible_careers(character, get_available_careers())
    return [c for c in careers if c["name"] != blocked]


def _forced_entry_career_term(session: "GameSession") -> "CareerTerm | None":
    """If an effect has queued a forced-career entry, consume it and
    return a first-term CareerTerm for that career (auto-qualified).

    Returns None if nothing is queued. Clears the flag and the re-entry
    block on the way through — the forced career overrides both.
    """
    from src.career_loader import career_to_term_kwargs, load_career

    career_name = session.character.pending_career_entry
    if not career_name:
        return None
    session.character.pending_career_entry = None
    session.current_career_data = load_career(career_name)
    session.career_term_count = 0
    session.blocked_career = None
    session.current_assignment = None
    kwargs = career_to_term_kwargs(
        session.current_career_data, is_first_term=True
    )
    # Forced entry auto-qualifies regardless of YAML.
    kwargs["qualification_auto"] = True
    return CareerTerm(
        session.character,
        term_number=session.career_term_count + 1,
        **kwargs,
    )

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
            status="QUALIFIED",
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
            self.character.add_skill(skill)
        self.outcome = StepOutcome(
            status="TRAINED",
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
            status="MISHAP",
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
            status="EVENT",
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
    status_pass = "PROMOTED"
    status_fail = "NOT_PROMOTED"
    status_at_max_rank = "AT_MAX_RANK"

    def __init__(
        self,
        character: Character,
        career_name: str,
        assignment: dict,
        ranks: list[dict],
        officer_ranks: list[dict] | None = None,
    ) -> None:
        advancement = assignment["advancement"]
        super().__init__(
            character=character,
            check_characteristic=advancement["characteristic"],
            target=advancement["target"],
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


class CommissionStep(Step):
    """Optional commission attempt for military careers.

    Player first chooses Attempt or Skip. On Attempt, roll 2d6 + DM vs the
    commission target. Success makes the character a rank 1 officer and
    replaces the advancement roll for this term (so `terms_served` is
    ticked here).

    Eligibility is decided at append-time by `CareerTerm`: first term,
    or SOC >= 9 in any term (with DM -1 per term after the first).
    """

    step_id = "commission"
    step_type = StepType.CHOICE

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
            options=[self.ATTEMPT, self.SKIP],
            required_count=1,
        )

    def resolve(self, player_input: dict | None = None) -> None:
        if player_input is None:
            raise ValueError("Commission decision is required.")
        selections = player_input.get("selections", [])
        if len(selections) != 1:
            raise ValueError("Must choose a single commission option.")
        decision = selections[0]
        if decision not in (self.ATTEMPT, self.SKIP):
            raise ValueError(f"Unknown commission option: {decision}")
        self._decision_pending = decision
        if decision == self.ATTEMPT:
            self.raw_roll = roll(2)
            self.total_roll = self.raw_roll + self._total_dm()

    def apply(self) -> None:
        if self._decision_pending == self.SKIP:
            self.outcome = StepOutcome(
                status="SKIPPED",
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
                status="COMMISSIONED",
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
                status="FAILED_COMMISSION",
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
        entry = next(
            (r for r in self.officer_ranks if r.get("rank") == new_rank),
            None,
        )
        if entry is None:
            return None
        bonus = entry.get("bonus_skill")
        if bonus and not try_apply_characteristic_bonus(self.character, bonus):
            self.character.add_skill(bonus)
        return entry.get("title")


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


class MusterOutOrNewCareerStep(Step):
    """Offered after a mishap: muster out with benefits or choose a new career."""

    step_id = "muster_out_or_new_career"
    step_type = StepType.CHOICE

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
            self.MUSTER_OUT: "MUSTER_OUT",
            self.CHOOSE_CAREER: "CHOOSE_CAREER",
        }[decision]
        self.outcome = StepOutcome(
            status=status,
            description=f"Decision: {decision}.",
            data={"decision": decision, "career_name": self.career_name},
        )


class ChooseDraftOrDrifterStep(Step):
    """Offered after a failed qualification: Draft (once per life) or Drifter.

    Draft rolls 1d6 to assign the character to a random service. Drifter
    is always available. Chosen career is entered next with automatic
    qualification (first term).
    """

    step_id = "choose_draft_or_drifter"
    step_type = StepType.CHOICE

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
            options=self._options(),
            required_count=1,
        )

    def resolve(self, player_input: dict | None = None) -> None:
        if player_input is None:
            raise ValueError("Draft-or-Drifter decision is required.")
        selections = player_input.get("selections", [])
        if len(selections) != 1:
            raise ValueError("Must choose one option.")
        decision = selections[0]
        if decision not in self._options():
            raise ValueError(f"Unavailable option: {decision}")
        self._decision_pending = decision
        if decision == self.DRAFT:
            self.draft_roll = roll(1)
            self.assigned_career = self.DRAFT_TABLE.get(self.draft_roll)

    def apply(self) -> None:
        if self._decision_pending == self.DRIFTER:
            self.assigned_career = "Drifter"
            self.outcome = StepOutcome(
                status="DRIFTER",
                description="Fell back to the Drifter career.",
                data={"career": "Drifter"},
            )
            return
        assert self.draft_roll is not None and self.assigned_career is not None
        self.outcome = StepOutcome(
            status="DRAFTED",
            description=(
                f"Drafted — rolled {self.draft_roll} on the Draft table: "
                f"assigned to the {self.assigned_career} career."
            ),
            data={
                "career": self.assigned_career,
                "roll": self.draft_roll,
            },
        )


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
                status="CASH",
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
            status="BENEFITS",
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
                status="MUSTERED_OUT",
                description=(
                    f"Mustered out of the {self.career_name} — "
                    f"{self.total_rolls} benefit roll(s) resolved."
                ),
            )

    def next_term(self, session: "GameSession") -> "Term | None":
        # Muster-out completes character creation in the current flow.
        session.current_assignment = None
        return None


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
                status="NO_AGING",
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
            status="AGING_CRISIS" if death else "AGED",
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


def _muster_out_term_for(
    session: "GameSession", career_name: str
) -> "MusterOutTerm":
    """Build a MusterOutTerm for a career exit and clear session career state."""
    career_data = session.current_career_data or {}
    benefits = career_data.get("benefits") or {}
    record = session.character.careers.get(career_name)
    terms_served = record.terms_served if record else 0
    rank = record.rank if record else 0
    session.current_career_data = None
    session.current_assignment = None
    return MusterOutTerm(
        session.character,
        career_name=career_name,
        benefits=benefits,
        terms_served=terms_served,
        rank=rank,
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
        if inner.step_id == MusterOutOrNewCareerStep.step_id:
            return f"{inner.career_name} — Mishap Exit"  # type: ignore[attr-defined]
        if inner.step_id == ChooseDraftOrDrifterStep.step_id:
            return "Draft or Drifter"
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

        if inner.step_id == ChooseDraftOrDrifterStep.step_id:
            career_name = outcome.data["career"]
            if outcome.status == "DRAFTED":
                session.draft_used = True
            session.current_career_data = load_career(career_name)
            session.career_term_count = 0
            session.blocked_career = None
            kwargs = career_to_term_kwargs(
                session.current_career_data, is_first_term=True
            )
            # Draft / Drifter fallback auto-qualifies regardless of YAML.
            kwargs["qualification_auto"] = True
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
                from src.career_loader import _normalize_qualification
                options, auto = _normalize_qualification(data["qualification"])
                return AssignmentChangeTerm(
                    session.character,
                    career_name=data["name"],
                    assignments=data["assignments"],
                    current_assignment=session.current_assignment,
                    qualification_options=options,
                    qualification_auto=auto,
                )
            # MUSTER_OUT — run the benefit rolls before creation ends.
            return _muster_out_term_for(session, inner.career_name)  # type: ignore[attr-defined]

        if inner.step_id == MusterOutOrNewCareerStep.step_id:
            if outcome.status == "MUSTER_OUT":
                return _muster_out_term_for(session, inner.career_name)  # type: ignore[attr-defined]
            # CHOOSE_CAREER — proceed to career selection, skipping benefits.
            session.current_career_data = None
            careers = _available_careers_for(
                session.character, session.blocked_career
            )
            return TransitionTerm(
                session.character, ChooseCareerStep(session.character, careers)
            )

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
        qualification_options: list[dict],
        qualification_auto: bool,
        service_skills: list[str],
        assignments: list[dict],
        skill_tables: dict[str, list[str]],
        skill_table_requirements: dict[str, dict] | None = None,
        events: dict | None = None,
        mishaps: dict | None = None,
        ranks: list[dict] | None = None,
        officer_ranks: list[dict] | None = None,
        commission: dict | None = None,
        assignment_change_group: str | None = None,
        assignment_override: dict | None = None,
        benefits: dict | None = None,
        basic_training_from_assignment: bool = False,
        is_first_term: bool = True,
        term_number: int = 1,
    ) -> None:
        super().__init__(character)
        self.career_name = career_name
        self.qualification_options = qualification_options
        self.qualification_auto = qualification_auto
        self.service_skills = service_skills
        self.assignments = assignments
        self.skill_tables = skill_tables
        self.skill_table_requirements = skill_table_requirements or {}
        self.events = events or {}
        self.mishaps = mishaps or {}
        self.ranks = ranks or []
        self.officer_ranks = officer_ranks or []
        self.commission = commission
        self.assignment_change_group = assignment_change_group
        self.benefits = benefits or {}
        self.basic_training_from_assignment = basic_training_from_assignment
        self.is_first_term = is_first_term
        self.term_number = term_number
        self._selected_assignment: dict | None = None
        self._pending_outcome: StepOutcome | None = None
        self._pending_finalize_outcome: StepOutcome | None = None

        # Best-of-options: for OR-qualification (e.g. Entertainer DEX or
        # INT), pick the option that yields the highest modifier for this
        # character so they make a single roll at their best DM.
        best_option = max(
            qualification_options,
            key=lambda o: character.characteristics[o["characteristic"]].modifier()
            if o["characteristic"] in character.characteristics
            else -99,
        )
        self.qualification_characteristic: str = best_option["characteristic"]
        self.qualification_target: int = best_option["target"]

        if is_first_term:
            if qualification_auto:
                self.steps = [
                    AutoQualifyStep(
                        character,
                        self.qualification_characteristic,
                        self.qualification_target,
                    )
                ]
            else:
                self.steps = [
                    RollQualificationStep(
                        character,
                        self.qualification_characteristic,
                        self.qualification_target,
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
                    career_name=self.career_name,
                )
            ]
        else:
            self.steps = [ChooseAssignmentStep(character, assignments)]

    def label(self) -> str:
        return f"{self.career_name} — Term {self.term_number}"

    def _commission_eligible(self) -> bool:
        """Whether to offer the commission step this term.

        Requires a commission config in the career; the character must
        not already be commissioned in this career; first term, OR
        SOC >= 9 in any subsequent term.
        """
        if self.commission is None:
            return False
        record = self.character.careers.get(self.career_name)
        if record is not None and record.commissioned:
            return False
        if self.is_first_term:
            return True
        soc = self.character.characteristics.get("Social Standing")
        return soc is not None and soc.value >= 9

    def _finalize_term(self, outcome: StepOutcome) -> None:
        """Increment age and either append an AgingStep or finalize immediately."""
        self.character.age += 4
        if self.character.age >= 34:
            self._pending_outcome = outcome
            self.steps.append(AgingStep(self.character))
        else:
            self.outcome = outcome

    def advance(self) -> None:
        """Complete the current step and dynamically append the next steps based on outcomes."""
        step = self.current_step
        super().advance()

        if step is None or step.outcome is None:
            return

        status = step.outcome.status

        if isinstance(step, (RollQualificationStep, AutoQualifyStep)):
            if status == "QUALIFIED":
                # Citizens and Drifters draw basic training from their
                # *assignment* skill table, so the assignment must be
                # chosen first and training happens after.
                if self.basic_training_from_assignment:
                    self.steps.append(
                        ChooseAssignmentStep(self.character, self.assignments)
                    )
                else:
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
                # Citizens/Drifters: insert basic training drawn from the
                # assignment's skill table before the survival check.
                if self.basic_training_from_assignment:
                    asn_skills = self.skill_tables.get(
                        self._selected_assignment["name"], []
                    )
                    if not self.character.careers:
                        self.steps.append(
                            BasicTrainingStep(self.character, asn_skills)
                        )
                    else:
                        self.steps.append(
                            PickServiceSkillStep(self.character, asn_skills)
                        )
                self.steps.append(
                    SurvivalCheckStep(self.character, self._selected_assignment)
                )
            else:
                self.steps.append(
                    ChooseCareerSkillsTable(
                        self.character,
                        list(self.skill_tables.keys()),
                        requirements=self.skill_table_requirements,
                        career_name=self.career_name,
                    )
                )

        elif isinstance(step, ChooseCareerSkillsTable):
            skill_options = self.skill_tables[step.outcome.data["skill_table"]]
            self.steps.append(RollForSkillStep(self.character, skill_options))

        elif isinstance(step, RollForSkillStep):
            if self._pending_finalize_outcome is not None:
                # Bonus skill roll granted by promotion — term ends here.
                terminal = self._pending_finalize_outcome
                self._pending_finalize_outcome = None
                self._finalize_term(terminal)
            else:
                self.steps.append(
                    SurvivalCheckStep(self.character, self._selected_assignment)
                )

        elif isinstance(step, SurvivalCheckStep):
            if status == "SURVIVED":
                self.steps.append(EventsRollStep(self.character, self.events))
            else:
                self.steps.append(MishapRollStep(self.character, self.mishaps))

        elif isinstance(step, EventsRollStep):
            # An event may force the character out of the career. Terms
            # served still counts — tick it here because advancement
            # won't run. No commission or advancement rolls follow.
            if step.forced_exit:
                self.character.record_career_term(self.career_name)
                self._finalize_term(StepOutcome(
                    status="FORCED_EXIT",
                    description=(
                        "Event forced you out of the career — term complete."
                    ),
                ))
                return
            # Commission is attempted between events and advancement for
            # eligible careers. If ineligible, skip straight to advancement.
            if self._commission_eligible():
                assert self.commission is not None
                dm = 0 if self.is_first_term else -(self.term_number - 1)
                self.steps.append(
                    CommissionStep(
                        self.character,
                        self.career_name,
                        self.commission["characteristic"],
                        self.commission["target"],
                        dm=dm,
                        officer_ranks=self.officer_ranks,
                    )
                )
            else:
                self.steps.append(
                    AdvancementRollStep(
                        self.character,
                        self.career_name,
                        self._selected_assignment,
                        self.ranks,
                        officer_ranks=self.officer_ranks,
                    )
                )

        elif isinstance(step, CommissionStep):
            if status == "COMMISSIONED":
                # Commission replaces advancement this term. terms_served
                # was ticked in CommissionStep.apply(). No forced-exit check
                # because there was no advancement roll.
                self._finalize_term(StepOutcome(
                    status="COMPLETED",
                    description="Term completed (commissioned).",
                ))
            else:
                self.steps.append(
                    AdvancementRollStep(
                        self.character,
                        self.career_name,
                        self._selected_assignment,
                        self.ranks,
                        officer_ranks=self.officer_ranks,
                    )
                )

        elif isinstance(step, MishapRollStep):
            self.character.mark_career_ejected(self.career_name)
            self.character.record_career_term(self.career_name)
            self._finalize_term(StepOutcome(
                status="MISHAP",
                description="Career ended by mishap.",
            ))

        elif isinstance(step, AdvancementRollStep):
            # End of a normal term. Natural 12 overrides everything else
            # (forced stay). Otherwise a modified roll ≤ terms served
            # forces the character out of the career.
            if step.forced_stay:
                terminal = StepOutcome(
                    status="FORCED_STAY",
                    description="Natural 12 — forced to stay in the career.",
                )
            elif step.forced_exit:
                terminal = StepOutcome(
                    status="FORCED_EXIT",
                    description=(
                        "Advancement roll did not exceed terms served — "
                        "forced to leave the career."
                    ),
                )
            else:
                terminal = StepOutcome(
                    status="COMPLETED",
                    description="Term completed.",
                )

            if status == "PROMOTED":
                # Promotion grants a bonus skill roll. Defer term
                # finalization until that roll completes.
                self._pending_finalize_outcome = terminal
                self.steps.append(
                    ChooseCareerSkillsTable(
                        self.character,
                        list(self.skill_tables.keys()),
                        requirements=self.skill_table_requirements,
                        career_name=self.career_name,
                    )
                )
            else:
                self._finalize_term(terminal)

        elif isinstance(step, AgingStep):
            self.outcome = self._pending_outcome

    def next_term(self, session: "GameSession") -> "Term | None":
        from src.career_loader import (
            career_to_term_kwargs,
            get_available_careers,
        )

        status = self.outcome.status if self.outcome else None

        if status == "FAILED_QUAL":
            forced = _forced_entry_career_term(session)
            if forced is not None:
                return forced
            # Per RAW, a failed qualification routes to the Draft (once
            # per life) or the Drifter career — never straight back to
            # career selection.
            return TransitionTerm(
                session.character,
                ChooseDraftOrDrifterStep(
                    session.character, draft_used=session.draft_used
                ),
            )

        if status == "MISHAP":
            session.career_term_count = 0
            session.blocked_career = self.career_name
            session.current_assignment = None
            forced = _forced_entry_career_term(session)
            if forced is not None:
                return forced
            # Keep session.current_career_data loaded — the muster-out
            # branch needs it to read benefit tables.
            return TransitionTerm(
                session.character,
                MusterOutOrNewCareerStep(session.character, self.career_name),
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
            forced = _forced_entry_career_term(session)
            if forced is not None:
                return forced
            careers = _available_careers_for(
                session.character, session.blocked_career
            )
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
        qualification_options: list[dict],
        qualification_auto: bool,
    ) -> None:
        super().__init__(character)
        self.career_name = career_name
        self.assignments = assignments
        self.current_assignment = current_assignment
        self.qualification_options = qualification_options
        self.qualification_auto = qualification_auto
        # Best-of-options: match CareerTerm's qualification choice.
        best = max(
            qualification_options,
            key=lambda o: character.characteristics[o["characteristic"]].modifier()
            if o["characteristic"] in character.characteristics
            else -99,
        )
        self.qualification_characteristic = best["characteristic"]
        self.qualification_target = best["target"]
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
            if self.qualification_auto:
                self.steps.append(
                    AutoQualifyStep(
                        self.character,
                        self.qualification_characteristic,
                        self.qualification_target,
                    )
                )
            else:
                self.steps.append(
                    RollQualificationStep(
                        self.character,
                        self.qualification_characteristic,
                        self.qualification_target,
                    )
                )
        elif isinstance(step, (RollQualificationStep, AutoQualifyStep)):
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
            careers = _available_careers_for(
                session.character, session.blocked_career
            )
            return TransitionTerm(
                session.character, ChooseCareerStep(session.character, careers)
            )

        return None
