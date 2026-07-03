from __future__ import annotations

from typing import TYPE_CHECKING

from src.career_data import CareerData
from src.character import Character
from src.terms.base import (
    Step,
    StepOutcome,
    Term,
)
from src.terms.careers.aging import AgingStep
from src.terms.careers.muster_out import MusterOutTerm, _muster_out_term_for
from src.terms.careers.steps import (
    AdvancementRollStep,
    AutoQualifyStep,
    BasicTrainingStep,
    ChooseAssignmentStep,
    ChooseCareerSkillsTable,
    ChooseCareerStep,
    ChooseDraftOrDrifterStep,
    CommissionStep,
    ContinueOrMusterOutStep,
    EventsRollStep,
    MishapRollStep,
    MusterOutOrNewCareerStep,
    PickServiceSkillStep,
    RollForSkillStep,
    RollQualificationStep,
    SurvivalCheckStep,
)

if TYPE_CHECKING:
    from src.terms.context import CareerContext


def _available_careers_for(character: Character, blocked: str | None) -> list[dict]:
    """Career list for ChooseCareerStep — filtered by eligibility and block."""
    from src.career_loader import filter_eligible_careers, get_available_careers

    careers = filter_eligible_careers(character, get_available_careers())
    return [c for c in careers if c["name"] != blocked]


def _forced_entry_career_term(context: "CareerContext") -> "CareerTerm | None":
    """If an effect has queued a forced-career entry, consume it and
    return a first-term CareerTerm for that career (auto-qualified).

    Returns None if nothing is queued. Clears the flag and the re-entry
    block on the way through — the forced career overrides both.
    """
    from src.career_loader import load_career

    career_name = context.character.pending_career_entry
    if not career_name:
        return None
    context.character.pending_career_entry = None
    context.current_career_data = load_career(career_name)
    context.career_term_count = 0
    context.blocked_career = None
    context.current_assignment = None
    return CareerTerm(
        context.character,
        context.current_career_data,
        term_number=context.career_term_count + 1,
        is_first_term=True,
        # Forced entry auto-qualifies regardless of YAML.
        force_auto_qualify=True,
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

    def _after_choose_career(
        self, inner: Step, outcome: StepOutcome, context: "CareerContext"
    ) -> "Term | None":
        from src.career_loader import load_career

        context.current_career_data = load_career(outcome.data["career"])
        context.career_term_count = 0
        # Block only applies to the immediately-following selection; once a
        # new career is picked the block is lifted.
        context.blocked_career = None
        # A university graduate's entry DM applies to their first career
        # qualification only — consume it here.
        qualification_dm = context.pre_career_qualification_dm
        context.pre_career_qualification_dm = 0
        return CareerTerm(
            context.character,
            context.current_career_data,
            term_number=context.career_term_count + 1,
            is_first_term=True,
            qualification_dm=qualification_dm,
        )

    def _after_draft_or_drifter(
        self, inner: Step, outcome: StepOutcome, context: "CareerContext"
    ) -> "Term | None":
        from src.career_loader import load_career

        if outcome.status == "DRAFTED":
            context.draft_used = True
        context.current_career_data = load_career(outcome.data["career"])
        context.career_term_count = 0
        context.blocked_career = None
        return CareerTerm(
            context.character,
            context.current_career_data,
            term_number=context.career_term_count + 1,
            is_first_term=True,
            # Draft / Drifter fallback auto-qualifies regardless of YAML.
            force_auto_qualify=True,
        )

    def _after_continue_or_muster(
        self, inner: Step, outcome: StepOutcome, context: "CareerContext"
    ) -> "Term | None":
        if outcome.status == "CONTINUE":
            return CareerTerm(
                context.character,
                context.current_career_data,
                term_number=context.career_term_count + 1,
                is_first_term=False,
            )
        if outcome.status == "CHANGE_ASSIGNMENT":
            # Hand off to the assignment-change sub-term. It will roll
            # qualification for the new assignment and, on success, start a
            # new CareerTerm with rank reset to 0.
            data = context.current_career_data
            return AssignmentChangeTerm(
                context.character,
                career_name=data.name,
                assignments=data.assignments_as_dicts(),
                current_assignment=context.current_assignment,
                qualification_options=data.qualification_options(),
                qualification_auto=data.qualification.auto,
            )
        # MUSTER_OUT — run the benefit rolls before creation ends.
        return _muster_out_term_for(context, inner.career_name)  # type: ignore[attr-defined]

    def _after_muster_or_new_career(
        self, inner: Step, outcome: StepOutcome, context: "CareerContext"
    ) -> "Term | None":
        if outcome.status == "MUSTER_OUT":
            return _muster_out_term_for(context, inner.career_name)  # type: ignore[attr-defined]
        # CHOOSE_CAREER — proceed to career selection, skipping benefits.
        context.current_career_data = None
        careers = _available_careers_for(context.character, context.blocked_career)
        return TransitionTerm(
            context.character, ChooseCareerStep(context.character, careers)
        )

    # Declarative cross-term routing: inner step id → handler. Add a decision
    # step by writing a handler above and registering it here.
    _NEXT_TERM_HANDLERS = {
        ChooseCareerStep.step_id: _after_choose_career,
        ChooseDraftOrDrifterStep.step_id: _after_draft_or_drifter,
        ContinueOrMusterOutStep.step_id: _after_continue_or_muster,
        MusterOutOrNewCareerStep.step_id: _after_muster_or_new_career,
    }

    def next_term(self, context: "CareerContext") -> "Term | None":
        inner = self.steps[0]
        outcome = inner.outcome
        if outcome is None:
            return None
        handler = self._NEXT_TERM_HANDLERS.get(inner.step_id)
        if handler is None:
            return None
        return handler(self, inner, outcome, context)


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
        career: CareerData,
        *,
        is_first_term: bool = True,
        term_number: int = 1,
        assignment_override: dict | None = None,
        force_auto_qualify: bool = False,
        qualification_dm: int = 0,
    ) -> None:
        super().__init__(character)
        self.career = career
        self.career_name = career.name
        # One-shot situational DM (e.g. a university graduate's entry bonus)
        # applied to the qualification roll for this first term only.
        self.qualification_dm = qualification_dm
        qualification_options = career.qualification_options()
        self.qualification_options = qualification_options
        self.qualification_auto = force_auto_qualify or career.qualification.auto
        self.service_skills = career.service_skills
        self.assignments = career.assignments_as_dicts()
        self.skill_tables = career.normalized_skill_tables()
        self.skill_table_requirements = career.skill_table_requirements()
        self.events = career.events
        self.mishaps = career.mishaps
        self.ranks = career.ranks_as_dicts()
        self.officer_ranks = career.officer_ranks_as_dicts()
        self.commission = career.commission_as_dict()
        self.assignment_change_group = career.assignment_change_group
        self.benefits = career.benefits_as_dict()
        self.basic_training_from_assignment = career.basic_training_from_assignment
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
            if self.qualification_auto:
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
                        extra_dm=self.qualification_dm,
                    )
                ]
        elif assignment_override is not None:
            # Continuing within the same career without re-prompting for
            # assignment (used by the assignment-change flow to carry
            # forward the chosen / retained assignment).
            self._selected_assignment = assignment_override
            self.steps = [self._skill_table_step()]
        else:
            self.steps = [ChooseAssignmentStep(character, self.assignments)]

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

    def _skill_table_step(self) -> ChooseCareerSkillsTable:
        """Build the career skill-table choice step (used in several transitions)."""
        return ChooseCareerSkillsTable(
            self.character,
            list(self.skill_tables.keys()),
            requirements=self.skill_table_requirements,
            career_name=self.career_name,
        )

    def _advancement_step(self) -> AdvancementRollStep:
        """Build the end-of-term advancement roll step."""
        return AdvancementRollStep(
            self.character,
            self.career_name,
            self._selected_assignment,
            self.ranks,
            officer_ranks=self.officer_ranks,
        )

    # --- Per-step transitions -------------------------------------------
    #
    # Each handler consumes the just-resolved step and appends the next
    # step(s) or synthesizes a terminal outcome. They are dispatched by
    # `advance()` via `_STEP_HANDLERS` (built below the class body), so a
    # new step type is wired in by adding a handler + one table entry
    # rather than editing a central if-elif chain. Each handler is a small
    # method that can be exercised in isolation in tests.

    def _after_qualification(self, step: Step) -> None:
        if step.outcome.status != "QUALIFIED":
            # Failed qualification ends the term immediately.
            self.outcome = StepOutcome(
                status="FAILED_QUAL",
                description="Qualification failed — returning to career selection.",
            )
            return
        # Citizens and Drifters draw basic training from their *assignment*
        # skill table, so the assignment must be chosen first and training
        # happens after.
        if self.basic_training_from_assignment:
            self.steps.append(ChooseAssignmentStep(self.character, self.assignments))
            return
        # First career ever → full Basic Training at level 0.
        # Subsequent career → pick one Service Skill at level 0.
        if not self.character.careers:
            self.steps.append(BasicTrainingStep(self.character, self.service_skills))
        else:
            self.steps.append(PickServiceSkillStep(self.character, self.service_skills))
        self.steps.append(ChooseAssignmentStep(self.character, self.assignments))

    def _after_assignment(self, step: Step) -> None:
        self._selected_assignment = step.outcome.data["assignment"]
        if not self.is_first_term:
            self.steps.append(self._skill_table_step())
            return
        # Citizens/Drifters: insert basic training drawn from the
        # assignment's skill table before the survival check.
        if self.basic_training_from_assignment:
            asn_skills = self.skill_tables.get(self._selected_assignment["name"], [])
            if not self.character.careers:
                self.steps.append(BasicTrainingStep(self.character, asn_skills))
            else:
                self.steps.append(PickServiceSkillStep(self.character, asn_skills))
        self.steps.append(
            SurvivalCheckStep(self.character, self._selected_assignment)
        )

    def _after_skill_table(self, step: Step) -> None:
        skill_options = self.skill_tables[step.outcome.data["skill_table"]]
        self.steps.append(RollForSkillStep(self.character, skill_options))

    def _after_skill_roll(self, step: Step) -> None:
        if self._pending_finalize_outcome is not None:
            # Bonus skill roll granted by promotion — term ends here.
            terminal = self._pending_finalize_outcome
            self._pending_finalize_outcome = None
            self._finalize_term(terminal)
        else:
            self.steps.append(
                SurvivalCheckStep(self.character, self._selected_assignment)
            )

    def _after_survival(self, step: Step) -> None:
        if step.outcome.status == "SURVIVED":
            self.steps.append(EventsRollStep(self.character, self.events))
        else:
            self.steps.append(MishapRollStep(self.character, self.mishaps))

    def _after_events(self, step: Step) -> None:
        # An event may force the character out of the career. Terms served
        # still counts — tick it here because advancement won't run. No
        # commission or advancement rolls follow.
        if step.forced_exit:
            self.character.record_career_term(self.career_name)
            self._finalize_term(StepOutcome(
                status="FORCED_EXIT",
                description="Event forced you out of the career — term complete.",
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
            self.steps.append(self._advancement_step())

    def _after_commission(self, step: Step) -> None:
        if step.outcome.status == "COMMISSIONED":
            # Commission replaces advancement this term. terms_served was
            # ticked in CommissionStep.apply(). No forced-exit check because
            # there was no advancement roll.
            self._finalize_term(StepOutcome(
                status="COMPLETED",
                description="Term completed (commissioned).",
            ))
        else:
            self.steps.append(self._advancement_step())

    def _after_mishap(self, step: Step) -> None:
        self.character.mark_career_ejected(self.career_name)
        self.character.record_career_term(self.career_name)
        self._finalize_term(StepOutcome(
            status="MISHAP",
            description="Career ended by mishap.",
        ))

    def _after_advancement(self, step: Step) -> None:
        # End of a normal term. Natural 12 overrides everything else
        # (forced stay). Otherwise a modified roll ≤ terms served forces
        # the character out of the career.
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

        if step.outcome.status == "PROMOTED":
            # Promotion grants a bonus skill roll. Defer term finalization
            # until that roll completes.
            self._pending_finalize_outcome = terminal
            self.steps.append(self._skill_table_step())
        else:
            self._finalize_term(terminal)

    def _after_aging(self, step: Step) -> None:
        self.outcome = self._pending_outcome

    def advance(self) -> None:
        """Complete the current step and dispatch to its transition handler.

        The handler dynamically appends the next step(s) or synthesizes a
        terminal outcome based on the just-resolved step's result.
        """
        step = self.current_step
        super().advance()

        if step is None or step.outcome is None:
            return

        handler = self._STEP_HANDLERS.get(type(step))
        if handler is not None:
            handler(self, step)

    # Declarative transition table: step type → handler. Grouping two step
    # classes (roll vs auto qualification) onto one handler is a table entry,
    # not a branch. Extend the flow by adding a handler above and a row here.
    _STEP_HANDLERS = {
        RollQualificationStep: _after_qualification,
        AutoQualifyStep: _after_qualification,
        ChooseAssignmentStep: _after_assignment,
        ChooseCareerSkillsTable: _after_skill_table,
        RollForSkillStep: _after_skill_roll,
        SurvivalCheckStep: _after_survival,
        EventsRollStep: _after_events,
        CommissionStep: _after_commission,
        MishapRollStep: _after_mishap,
        AdvancementRollStep: _after_advancement,
        AgingStep: _after_aging,
    }

    def next_term(self, context: "CareerContext") -> "Term | None":
        status = self.outcome.status if self.outcome else None

        if status == "FAILED_QUAL":
            forced = _forced_entry_career_term(context)
            if forced is not None:
                return forced
            # Per RAW, a failed qualification routes to the Draft (once
            # per life) or the Drifter career — never straight back to
            # career selection.
            return TransitionTerm(
                context.character,
                ChooseDraftOrDrifterStep(
                    context.character, draft_used=context.draft_used
                ),
            )

        if status == "MISHAP":
            context.career_term_count = 0
            context.blocked_career = self.career_name
            context.current_assignment = None
            forced = _forced_entry_career_term(context)
            if forced is not None:
                return forced
            # Keep context.current_career_data loaded — the muster-out
            # branch needs it to read benefit tables.
            return TransitionTerm(
                context.character,
                MusterOutOrNewCareerStep(context.character, self.career_name),
            )

        if status == "COMPLETED":
            context.career_term_count += 1
            context.current_assignment = self._selected_assignment
            return TransitionTerm(
                context.character,
                ContinueOrMusterOutStep(
                    context.character,
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
            context.current_career_data = None
            context.career_term_count = 0
            context.blocked_career = self.career_name
            context.current_assignment = None
            forced = _forced_entry_career_term(context)
            if forced is not None:
                return forced
            careers = _available_careers_for(
                context.character, context.blocked_career
            )
            return TransitionTerm(
                context.character, ChooseCareerStep(context.character, careers)
            )

        if status == "FORCED_STAY":
            # Natural 12 on advancement — skip continue/muster and start
            # the next term in the same career immediately.
            context.career_term_count += 1
            return CareerTerm(
                context.character,
                context.current_career_data,
                term_number=context.career_term_count + 1,
                is_first_term=False,
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

    def _after_assignment(self, step: Step) -> None:
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

    def _after_qualification(self, step: Step) -> None:
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

    # Declarative transition table: step type → handler (mirrors CareerTerm).
    _STEP_HANDLERS = {
        ChooseAssignmentStep: _after_assignment,
        RollQualificationStep: _after_qualification,
        AutoQualifyStep: _after_qualification,
    }

    def advance(self) -> None:
        step = self.current_step
        super().advance()
        if step is None or step.outcome is None:
            return
        handler = self._STEP_HANDLERS.get(type(step))
        if handler is not None:
            handler(self, step)

    def next_term(self, context: "CareerContext") -> "Term | None":
        status = self.outcome.status if self.outcome else None

        if status == "CHANGED":
            # RAW: rank resets to 0 when the assignment changes.
            record = self.character.ensure_career(self.career_name)
            record.rank = 0
            context.current_assignment = self._chosen_assignment
            return CareerTerm(
                context.character,
                context.current_career_data,
                term_number=context.career_term_count + 1,
                is_first_term=False,
                assignment_override=self._chosen_assignment,
            )

        if status == "CHANGE_FAILED":
            context.current_career_data = None
            context.career_term_count = 0
            context.blocked_career = self.career_name
            context.current_assignment = None
            careers = _available_careers_for(
                context.character, context.blocked_career
            )
            return TransitionTerm(
                context.character, ChooseCareerStep(context.character, careers)
            )

        return None
