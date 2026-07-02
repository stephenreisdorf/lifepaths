"""Terms route via next_term(context) against a plain CareerContext.

These tests exercise term transitions in isolation — constructing a
CareerContext directly and asserting on what the term reads and mutates —
without building a full GameSession. That isolation is the point of the
typed-context refactor.
"""

from src.career_loader import load_career
from src.character import Character
from src.terms.base import StepOutcome
from src.terms.careers import (
    CareerTerm,
    ChooseCareerStep,
    ContinueOrMusterOutStep,
    TransitionTerm,
)
from src.terms.childhood import ChildhoodTerm
from src.terms.context import CareerContext


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
    return char


def test_childhood_next_term_takes_a_context():
    """ChildhoodTerm routes to career selection given only a context."""
    char = _character()
    context = CareerContext(character=char)

    nxt = ChildhoodTerm(char).next_term(context)

    assert isinstance(nxt, TransitionTerm)
    assert nxt.steps[0].step_id == ChooseCareerStep.step_id


def test_career_term_completed_mutates_context():
    """A COMPLETED CareerTerm advances the term count and records the
    assignment on the context it is handed — no GameSession required."""
    char = _character()
    career = load_career("scout")
    term = CareerTerm(char, career, is_first_term=True, term_number=1)

    # Simulate a completed term: set the terminal outcome and the
    # assignment the character served, as the step machine would.
    assignment = career.assignments_as_dicts()[0]
    term._selected_assignment = assignment
    term.outcome = StepOutcome(status="COMPLETED", description="Term completed.")

    context = CareerContext(
        character=char,
        current_career_data=career,
        career_term_count=0,
    )
    nxt = term.next_term(context)

    assert context.career_term_count == 1
    assert context.current_assignment == assignment
    assert isinstance(nxt, TransitionTerm)
    assert nxt.steps[0].step_id == ContinueOrMusterOutStep.step_id
