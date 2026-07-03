"""Anagathics wired into the career-term flow (MgT 2022, Ageing).

Covers the start-of-term offer/upkeep, the doubled Survival check while on a
course, and the natural-2 → Prisoner routing. The domain-model rules (the SOC
10+ roll, cost, Ageing DM) are tested in ``tests/test_anagathics.py``; here we
test the ``CareerTerm`` wiring on top of them.
"""

from src.career_loader import load_career
from src.character import AnagathicsCourse, Character
from src.terms.base import StepOutcome, StepStatus
from src.terms.careers import (
    AnagathicsUpkeepStep,
    AutoQualifyStep,
    CareerTerm,
    ChooseAnagathicsStep,
    ChooseAssignmentStep,
    EventsRollStep,
    MishapRollStep,
    RollQualificationStep,
    SurvivalCheckStep,
)
from src.terms.context import CareerContext

_QUALIFICATION_STEPS = (RollQualificationStep, AutoQualifyStep)


def _character(**stats: int) -> Character:
    base = {
        "Strength": 7,
        "Dexterity": 7,
        "Endurance": 7,
        "Intelligence": 7,
        "Education": 7,
        "Social Standing": 7,
    }
    base.update(stats)
    char = Character(name="Test", characteristics={}, skills={})
    for name, value in base.items():
        char.add_characteristic(characteristic=name, value=value)
    char.age = 18
    return char


def _scout_term(char: Character, *, enabled: bool, is_first_term: bool = True) -> CareerTerm:
    return CareerTerm(
        char,
        load_career("scout"),
        is_first_term=is_first_term,
        anagathics_enabled=enabled,
    )


# --- Opening step: offer / upkeep / suppression ----------------------------


def test_rule_off_opens_directly_on_qualification():
    term = _scout_term(_character(), enabled=False)
    assert isinstance(term.steps[0], _QUALIFICATION_STEPS)


def test_rule_on_no_course_opens_on_the_anagathics_offer():
    term = _scout_term(_character(), enabled=True)
    assert isinstance(term.steps[0], ChooseAnagathicsStep)


def test_rule_on_active_course_opens_on_upkeep():
    char = _character()
    char.anagathics = AnagathicsCourse(terms_used=1)
    term = _scout_term(char, enabled=True, is_first_term=False)
    assert isinstance(term.steps[0], AnagathicsUpkeepStep)


def test_prisoner_career_never_offers_anagathics():
    # RAW: "Travellers may not use Anagathics in prison."
    char = _character()
    char.anagathics = AnagathicsCourse(terms_used=1)
    term = CareerTerm(char, load_career("prisoner"), anagathics_enabled=True)
    assert not isinstance(term.steps[0], (ChooseAnagathicsStep, AnagathicsUpkeepStep))


# --- The offer choice outcomes ---------------------------------------------


def test_declining_continues_into_the_normal_term():
    char = _character()
    term = _scout_term(char, enabled=True)
    term.submit({"selections": [ChooseAnagathicsStep.DECLINE]})

    assert term.steps[0].outcome.status == StepStatus.ANAGATHICS_DECLINED
    assert char.anagathics is None
    # The real opening step is appended and becomes current.
    assert isinstance(term.current_step, _QUALIFICATION_STEPS)


def test_starting_a_course_charges_and_then_continues(monkeypatch):
    # SOC 7 → DM 0; entry roll 10 → total 10 ≥ 10 starts. Cost die 3.
    rolls = iter([10, 3])
    monkeypatch.setattr("src.terms.anagathics.roll", lambda _n: next(rolls))
    char = _character()
    term = _scout_term(char, enabled=True)

    term.submit({"selections": [ChooseAnagathicsStep.START]})

    assert term.steps[0].outcome.status == StepStatus.ANAGATHICS_STARTED
    assert char.anagathics is not None and char.anagathics.active
    assert char.cash == -75000  # 3 × Cr25000, into debt
    assert isinstance(term.current_step, _QUALIFICATION_STEPS)
    assert term.outcome is None  # term is not terminal


def test_missing_the_roll_continues_without_a_course(monkeypatch):
    monkeypatch.setattr("src.terms.anagathics.roll", lambda _n: 5)  # 5 < 10
    char = _character()
    term = _scout_term(char, enabled=True)

    term.submit({"selections": [ChooseAnagathicsStep.START]})

    assert term.steps[0].outcome.status == StepStatus.ANAGATHICS_MISSED
    assert char.anagathics is None
    assert isinstance(term.current_step, _QUALIFICATION_STEPS)


def test_natural_two_ends_the_term_and_routes_to_prisoner(monkeypatch):
    monkeypatch.setattr("src.terms.anagathics.roll", lambda _n: 2)
    char = _character(**{"Social Standing": 15})
    term = _scout_term(char, enabled=True)

    term.submit({"selections": [ChooseAnagathicsStep.START]})

    assert term.outcome.status == StepStatus.ANAGATHICS_PRISONER
    assert char.pending_career_entry == "Prisoner"
    assert char.anagathics is None

    context = CareerContext(
        character=char,
        current_career_data=load_career("scout"),
        anagathics_enabled=True,
    )
    nxt = term.next_term(context)
    assert isinstance(nxt, CareerTerm)
    assert nxt.career_name == "Prisoner"
    assert char.pending_career_entry is None  # consumed


# --- Upkeep on a continuing term -------------------------------------------


def test_upkeep_charges_and_extends_the_course(monkeypatch):
    monkeypatch.setattr("src.terms.anagathics.roll", lambda _n: 4)  # cost die
    char = _character()
    char.anagathics = AnagathicsCourse(terms_used=1, total_cost=25000)
    char.cash = 0
    term = _scout_term(char, enabled=True, is_first_term=False)

    term.submit(None)  # automatic upkeep step

    assert term.steps[0].outcome.status == StepStatus.ANAGATHICS_MAINTAINED
    assert char.anagathics.terms_used == 2
    assert char.cash == -100000  # 4 × Cr25000
    assert isinstance(term.current_step, ChooseAssignmentStep)


# --- Doubled Survival checks -----------------------------------------------


def _term_ready_for_survival(char: Character) -> CareerTerm:
    term = _scout_term(char, enabled=True)
    term._selected_assignment = term.assignments[0]
    return term


def test_no_course_appends_a_single_survival_check():
    term = _term_ready_for_survival(_character())
    term._append_survival_check()
    assert term._second_survival_pending is False


def _survival_step(term: CareerTerm, char: Character, status: StepStatus) -> SurvivalCheckStep:
    step = SurvivalCheckStep(char, term.assignments[0])
    step.outcome = StepOutcome(status=status)
    return step


def test_active_course_queues_a_second_survival_on_success():
    char = _character()
    char.anagathics = AnagathicsCourse(terms_used=1)
    term = _term_ready_for_survival(char)

    # Appending the first check, on a course, flags that a second must follow.
    term._append_survival_check()
    assert term._second_survival_pending is True
    assert isinstance(term.steps[-1], SurvivalCheckStep)

    # First check survived → a second Survival check follows, flag cleared.
    before = len(term.steps)
    term._after_survival(_survival_step(term, char, StepStatus.SURVIVED))
    assert term._second_survival_pending is False
    assert isinstance(term.steps[-1], SurvivalCheckStep)
    assert len(term.steps) == before + 1

    # Second check survived → proceed to events (no third check).
    term._after_survival(_survival_step(term, char, StepStatus.SURVIVED))
    assert isinstance(term.steps[-1], EventsRollStep)


def test_failing_either_check_mishaps_and_stops_doubling():
    char = _character()
    char.anagathics = AnagathicsCourse(terms_used=1)
    term = _term_ready_for_survival(char)
    term._append_survival_check()
    assert term._second_survival_pending is True

    term._after_survival(_survival_step(term, char, StepStatus.FAILED))

    assert term._second_survival_pending is False
    assert isinstance(term.steps[-1], MishapRollStep)
