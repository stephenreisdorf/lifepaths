"""Career step transitions are dispatched via declarative tables.

`CareerTerm.advance()` and `TransitionTerm.next_term()` both route by a
step-keyed table to small per-transition handlers. These tests exercise
individual transitions in isolation — calling one handler with a stand-in
step — rather than stepping through a whole career. That isolation is the
point of the sequencing-machine refactor.
"""

from src.career_loader import load_career
from src.character import Character
from src.terms.base import StepOutcome, StepStatus
from src.terms.careers import (
    AdvancementRollStep,
    AgingStep,
    AnagathicsUpkeepStep,
    AssignmentChangeTerm,
    AutoQualifyStep,
    BasicTrainingStep,
    CareerTerm,
    ChooseAnagathicsStep,
    ChooseAssignmentStep,
    ChooseCareerSkillsTable,
    ChooseCareerStep,
    ChooseDraftOrDrifterStep,
    CommissionStep,
    ContinueOrMusterOutStep,
    EventsRollStep,
    MishapRollStep,
    MusterOutOrNewCareerStep,
    RollForSkillStep,
    RollQualificationStep,
    SurvivalCheckStep,
    TransitionTerm,
)
from src.terms.context import CareerContext


class _FakeStep:
    """Minimal stand-in for a resolved step: carries an outcome plus any
    ad-hoc attributes a handler reads (e.g. `forced_exit`)."""

    def __init__(self, status: str = "done", data: dict | None = None, **attrs):
        self.outcome = StepOutcome(status=status, data=data or {})
        for key, value in attrs.items():
            setattr(self, key, value)


def _character() -> Character:
    char = Character(name="Test", characteristics={}, skills={})
    for name in [
        "Strength",
        "Dexterity",
        "Endurance",
        "Intelligence",
        "Education",
        "Social Standing",
    ]:
        char.add_characteristic(characteristic=name, value=7)
    char.age = 18  # keep age+4 under the aging threshold in these tests
    return char


def _scout_term(is_first_term: bool = True) -> CareerTerm:
    return CareerTerm(_character(), load_career("scout"), is_first_term=is_first_term)


def _scout_term_subsequent_career() -> CareerTerm:
    """First-term Scout CareerTerm for a character who already has a prior
    career on record (so this is *not* their first career ever)."""
    char = _character()
    char.ensure_career("Navy")
    return CareerTerm(char, load_career("scout"), is_first_term=True)


# --- CareerTerm dispatch table --------------------------------------------


def test_step_handler_table_covers_every_flow_step():
    """The dispatch table is the single wiring point — lock its coverage so a
    new step type can't silently fall through `advance()`."""
    assert set(CareerTerm._STEP_HANDLERS) == {
        ChooseAnagathicsStep,
        AnagathicsUpkeepStep,
        RollQualificationStep,
        AutoQualifyStep,
        ChooseAssignmentStep,
        ChooseCareerSkillsTable,
        RollForSkillStep,
        SurvivalCheckStep,
        EventsRollStep,
        CommissionStep,
        MishapRollStep,
        AdvancementRollStep,
        AgingStep,
    }


def test_terminal_handler_table_covers_every_career_term_outcome():
    """Cross-term terminal routing should stay declarative like step routing."""
    assert set(CareerTerm._TERMINAL_HANDLERS) == {
        StepStatus.ANAGATHICS_PRISONER,
        StepStatus.FAILED_QUAL,
        StepStatus.MISHAP,
        StepStatus.COMPLETED,
        StepStatus.FORCED_EXIT,
        StepStatus.FORCED_STAY,
    }


# --- Individual CareerTerm transitions ------------------------------------


def test_after_qualification_qualified_appends_training_then_assignment():
    term = _scout_term()
    term._after_qualification(_FakeStep(status="QUALIFIED"))

    appended = [s.step_id for s in term.steps[1:]]
    assert appended == [BasicTrainingStep.step_id, ChooseAssignmentStep.step_id]
    assert term.outcome is None


def test_after_qualification_failed_ends_term():
    term = _scout_term()
    term._after_qualification(_FakeStep(status="FAILED"))

    assert term.outcome is not None
    assert term.outcome.status == "FAILED_QUAL"
    assert len(term.steps) == 1  # nothing appended


def test_army_entry_grants_rank_zero_gun_combat():
    """Entering Army as a first career grants Gun Combat at rank 0, before any
    advancement roll (RAW: Army starting skill Gun Combat)."""
    char = _character()
    term = CareerTerm(char, load_career("army"), is_first_term=True)
    assert not char.has_skill("Gun Combat")  # not granted before qualifying

    term._after_qualification(_FakeStep(status="QUALIFIED"))

    assert char.has_skill("Gun Combat")
    # No advancement has run, so no promotion happened.
    assert "Army" not in char.careers or char.careers["Army"].rank == 0


def test_prisoner_entry_grants_rank_zero_melee_unarmed():
    """Entering Prisoner grants Melee (unarmed) at rank 0 (RAW starting skill)."""
    char = _character()
    term = CareerTerm(char, load_career("prisoner"), is_first_term=True)
    assert not char.has_skill("Melee")

    term._after_qualification(_FakeStep(status="QUALIFIED"))

    assert char.has_skill("Melee")
    assert char.skills["Melee"].has_specialty("unarmed")


def test_failed_qualification_grants_no_rank_zero_skill():
    """The rank-0 entry skill is only granted when qualification succeeds."""
    char = _character()
    term = CareerTerm(char, load_career("army"), is_first_term=True)
    term._after_qualification(_FakeStep(status="FAILED"))

    assert not char.has_skill("Gun Combat")


def test_first_career_first_term_skips_skill_roll():
    """First career ever: basic training is the only skill grant — the first
    term goes straight from assignment to the survival check, no skill roll."""
    term = _scout_term()  # character has no prior careers
    assignment = term.assignments[0]
    term._after_assignment(_FakeStep(selected_assignment=assignment))

    assert isinstance(term.steps[-1], SurvivalCheckStep)
    assert not any(isinstance(s, ChooseCareerSkillsTable) for s in term.steps)


def test_subsequent_career_first_term_takes_skill_roll():
    """A later career's first term still takes the normal per-term skill roll
    (in addition to the one level-0 basic-training skill), before survival."""
    term = _scout_term_subsequent_career()
    assignment = term.assignments[0]
    term._after_assignment(_FakeStep(selected_assignment=assignment))

    assert isinstance(term.steps[-1], ChooseCareerSkillsTable)


def test_after_survival_branches_on_status():
    survived = _scout_term()
    survived._after_survival(_FakeStep(status="SURVIVED"))
    assert survived.steps[-1].step_id == EventsRollStep.step_id

    mishap = _scout_term()
    mishap._after_survival(_FakeStep(status="FAILED"))
    assert mishap.steps[-1].step_id == MishapRollStep.step_id


def test_after_skill_table_appends_roll_for_the_chosen_table():
    term = _scout_term()
    table_name = next(iter(term.skill_tables))
    term._after_skill_table(_FakeStep(data={"skill_table": table_name}))

    assert isinstance(term.steps[-1], RollForSkillStep)


def test_after_advancement_promoted_defers_finalize_and_grants_skill():
    term = _scout_term()
    term._after_advancement(
        _FakeStep(status="PROMOTED", forced_stay=False, forced_exit=False)
    )

    assert term.outcome is None  # not finalized yet
    assert term._pending_finalize_outcome is not None
    assert term._pending_finalize_outcome.status == "COMPLETED"
    assert isinstance(term.steps[-1], ChooseCareerSkillsTable)


def test_after_advancement_no_promotion_finalizes_completed():
    term = _scout_term()
    term._after_advancement(
        _FakeStep(status="NOT_PROMOTED", forced_stay=False, forced_exit=False)
    )

    assert term.outcome is not None
    assert term.outcome.status == "COMPLETED"


def test_after_mishap_records_ejection_and_ends_term():
    term = _scout_term()
    term._after_mishap(_FakeStep())

    assert term.outcome is not None
    assert term.outcome.status == "MISHAP"
    record = term.character.careers[term.career_name]
    assert record.ejected
    assert record.terms_served == 1


# --- TransitionTerm cross-term routing ------------------------------------


def test_next_term_table_covers_every_decision_step():
    assert set(TransitionTerm._NEXT_TERM_HANDLERS) == {
        ChooseCareerStep.step_id,
        ChooseDraftOrDrifterStep.step_id,
        ContinueOrMusterOutStep.step_id,
        MusterOutOrNewCareerStep.step_id,
    }


def test_transition_choose_career_starts_first_term_and_clears_block():
    char = _character()
    step = ChooseCareerStep(char, [])
    step.outcome = StepOutcome(status="CHOSEN", data={"career": "scout"})
    transition = TransitionTerm(char, step)
    context = CareerContext(character=char, blocked_career="stale")

    nxt = transition.next_term(context)

    assert isinstance(nxt, CareerTerm)
    assert nxt.is_first_term
    assert context.blocked_career is None
    assert context.current_career_data.name == load_career("scout").name


def test_transition_choose_new_career_after_mishap_routes_to_selection():
    char = _character()
    step = MusterOutOrNewCareerStep(char, "Scout")
    step.outcome = StepOutcome(status="CHOOSE_CAREER")
    transition = TransitionTerm(char, step)
    context = CareerContext(
        character=char, current_career_data=load_career("scout")
    )

    nxt = transition.next_term(context)

    assert isinstance(nxt, TransitionTerm)
    assert nxt.steps[0].step_id == ChooseCareerStep.step_id
    assert context.current_career_data is None


# --- AssignmentChangeTerm transitions -------------------------------------


def _assignment_change_term() -> AssignmentChangeTerm:
    career = load_career("scout")
    assignments = career.assignments
    return AssignmentChangeTerm(
        _character(),
        career_name=career.name,
        assignments=assignments,
        current_assignment=assignments[0],
        qualification_options=career.qualification.options,
        qualification_auto=career.qualification.auto,
    )


def test_assignment_change_handler_table_covers_its_steps():
    assert set(AssignmentChangeTerm._STEP_HANDLERS) == {
        ChooseAssignmentStep,
        RollQualificationStep,
        AutoQualifyStep,
    }


def test_assignment_change_after_assignment_appends_qualification():
    term = _assignment_change_term()
    other = term.assignments[1]
    term._after_assignment(_FakeStep(selected_assignment=other))

    assert term._chosen_assignment == other
    appended = term.steps[-1]
    assert appended.step_id in (
        RollQualificationStep.step_id,
        AutoQualifyStep.step_id,
    )


def test_assignment_change_qualified_sets_changed_outcome():
    term = _assignment_change_term()
    term._chosen_assignment = term.assignments[1]
    term._after_qualification(_FakeStep(status="QUALIFIED"))

    assert term.outcome is not None
    assert term.outcome.status == "CHANGED"


def test_assignment_change_failed_sets_change_failed_outcome():
    term = _assignment_change_term()
    term._chosen_assignment = term.assignments[1]
    term._after_qualification(_FakeStep(status="FAILED"))

    assert term.outcome is not None
    assert term.outcome.status == "CHANGE_FAILED"
