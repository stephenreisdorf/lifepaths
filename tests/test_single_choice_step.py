import pytest

from src.character import Character
from src.terms.base import SingleChoiceStep, StepType


class _ChoiceStep(SingleChoiceStep):
    step_id = "choice"

    def __init__(self) -> None:
        super().__init__(Character(name="Test", characteristics={}, skills={}))
        self.selected: str | None = None

    def options(self) -> list[str]:
        return ["Alpha", "Beta"]

    def on_choice(self, selection: str) -> None:
        self.selected = selection


def test_single_choice_step_validates_exactly_one_available_selection():
    step = _ChoiceStep()

    assert step.step_type == StepType.CHOICE
    with pytest.raises(ValueError, match="Selection is required."):
        step.resolve()
    with pytest.raises(ValueError, match="Must choose a single option."):
        step.resolve({"selections": ["Alpha", "Beta"]})
    with pytest.raises(ValueError, match="Unavailable option: Gamma"):
        step.resolve({"selections": ["Gamma"]})

    step.resolve({"selections": ["Beta"]})

    assert step.selected == "Beta"
