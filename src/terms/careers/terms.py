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
    from src.engine import GameSession


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
    from src.career_loader import load_career

    career_name = session.character.pending_career_entry
    if not career_name:
        return None
    session.character.pending_career_entry = None
    session.current_career_data = load_career(career_name)
    session.career_term_count = 0
    session.blocked_career = None
    session.current_assignment = None
    return CareerTerm(
        session.character,
        session.current_career_data,
        term_number=session.career_term_count + 1,
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

    def next_term(self, session: "GameSession") -> "Term | None":
        # Local imports to avoid circular references.
        from src.career_loader import load_career

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
            return CareerTerm(
                session.character,
                session.current_career_data,
                term_number=session.career_term_count + 1,
                is_first_term=True,
            )

        if inner.step_id == ChooseDraftOrDrifterStep.step_id:
            career_name = outcome.data["career"]
            if outcome.status == "DRAFTED":
                session.draft_used = True
            session.current_career_data = load_career(career_name)
            session.career_term_count = 0
            session.blocked_career = None
            return CareerTerm(
                session.character,
                session.current_career_data,
                term_number=session.career_term_count + 1,
                is_first_term=True,
                # Draft / Drifter fallback auto-qualifies regardless of YAML.
                force_auto_qualify=True,
            )

        if inner.step_id == ContinueOrMusterOutStep.step_id:
            if outcome.status == "CONTINUE":
                return CareerTerm(
                    session.character,
                    session.current_career_data,
                    term_number=session.career_term_count + 1,
                    is_first_term=False,
                )
            if outcome.status == "CHANGE_ASSIGNMENT":
                # Hand off to the assignment-change sub-term. It will
                # roll qualification for the new assignment and, on
                # success, start a new CareerTerm with rank reset to 0.
                data = session.current_career_data
                return AssignmentChangeTerm(
                    session.character,
                    career_name=data.name,
                    assignments=data.assignments_as_dicts(),
                    current_assignment=session.current_assignment,
                    qualification_options=data.qualification_options(),
                    qualification_auto=data.qualification.auto,
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
        career: CareerData,
        *,
        is_first_term: bool = True,
        term_number: int = 1,
        assignment_override: dict | None = None,
        force_auto_qualify: bool = False,
    ) -> None:
        super().__init__(character)
        self.career = career
        self.career_name = career.name
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
            return CareerTerm(
                session.character,
                session.current_career_data,
                term_number=session.career_term_count + 1,
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
        status = self.outcome.status if self.outcome else None

        if status == "CHANGED":
            # RAW: rank resets to 0 when the assignment changes.
            record = self.character.ensure_career(self.career_name)
            record.rank = 0
            session.current_assignment = self._chosen_assignment
            return CareerTerm(
                session.character,
                session.current_career_data,
                term_number=session.career_term_count + 1,
                is_first_term=False,
                assignment_override=self._chosen_assignment,
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
