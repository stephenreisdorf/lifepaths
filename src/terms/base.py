from enum import Enum

from pydantic import BaseModel

from src.character import Character


class StepType(str, Enum):
    """The kind of interaction a step requires."""

    AUTOMATIC = "automatic"  # No player input (e.g. dice roll)
    CHOICE = "choice"  # Player picks N items from a list


class StepPrompt(BaseModel):
    """Describes what a step needs from the player and what to display."""

    step_id: str
    step_type: StepType
    description: str
    data: dict | None = None
    options: list[str] | None = None
    required_count: int | None = None


class SubmitResult(BaseModel):
    """Uniform response after submitting player input (or auto-resolving)."""

    resolved_steps: list[StepPrompt]
    next_prompt: StepPrompt | None
    character: dict


class Step:
    """Base class for a single step within a term.

    Steps follow a resolve → apply → complete lifecycle.
    Subclasses must set step_id and step_type, and override prompt(),
    resolve(), and apply() with concrete behavior.
    """

    step_id: str = ""
    step_type: StepType = StepType.AUTOMATIC

    def __init__(self, character: Character) -> None:
        self.completed: bool = False
        self.character: Character = character

    def prompt(self) -> StepPrompt:
        """Describe what this step needs from the player."""
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description="",
        )

    def resolve(self, player_input: dict | None = None) -> None:
        """Determine the outcome of this step.

        Automatic steps ignore player_input.
        Interactive steps read from player_input.
        """
        pass

    def apply(self) -> None:
        """Apply the resolved outcome to the character."""
        pass

    def complete(self) -> None:
        """Mark this step as completed."""
        self.completed = True


class Term:
    """Base class for a life path term (a phase of character creation).

    A term holds a reference to a character and sequences one or more steps.
    Subclasses should populate self.steps in __init__.
    """

    def __init__(self, character: Character) -> None:
        self.character: Character = character
        self.steps: list[Step] = []
        self.current_step_index: int = 0

    @property
    def current_step(self) -> Step | None:
        """Return the current step, or None if all steps are complete."""
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def advance(self) -> None:
        """Mark the current step as complete and move to the next."""
        if self.current_step:
            self.current_step.complete()
            self.current_step_index += 1

    def current_step_prompt(self) -> StepPrompt | None:
        """Return the prompt for the current step, or None if the term is done."""
        step = self.current_step
        if step is None:
            return None
        return step.prompt()

    def submit(self, player_input: dict | None = None) -> None:
        """Resolve and apply the current step, then advance."""
        step = self.current_step
        if step is None:
            raise ValueError("No current step to submit.")
        step.resolve(player_input)
        step.apply()
        self.advance()
