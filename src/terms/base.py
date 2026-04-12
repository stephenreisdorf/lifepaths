from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from src.character import Character
from src.utilities import roll

if TYPE_CHECKING:
    from src.engine import GameSession


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
    term_label: str | None = None


class SubmitResult(BaseModel):
    """Uniform response after submitting player input (or auto-resolving)."""

    resolved_steps: list[StepPrompt]
    next_prompt: StepPrompt | None
    character: dict


class StepOutcome(BaseModel):
    """Uniform record of what a step produced.

    `status` is a short machine-readable tag (e.g. "QUALIFIED", "FAILED",
    "SURVIVED", "MISHAP", "CONTINUE", "MUSTER_OUT"). `description` is the
    human-readable sentence rendered into the post-resolve prompt. `data`
    carries structured details (roll totals, selections, career name, …).
    """

    status: str = "done"
    description: str = ""
    data: dict = Field(default_factory=dict)


class Step:
    """Base class for a single step within a term.

    Steps follow a resolve → apply → complete lifecycle. `apply()` should
    populate `self.outcome`; `prompt()` reads `self.outcome.description`
    when present for the post-resolve view.
    """

    step_id: str = ""
    step_type: StepType = StepType.AUTOMATIC

    def __init__(self, character: Character) -> None:
        self.completed: bool = False
        self.character: Character = character
        self.outcome: StepOutcome | None = None

    def prompt(self) -> StepPrompt:
        """Describe what this step needs from the player.

        Default implementation renders `self.outcome.description` once the
        step has been resolved; subclasses override to provide a "before"
        description as well.
        """
        description = self.outcome.description if self.outcome else ""
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description=description,
        )

    def resolve(self, player_input: dict | None = None) -> None:
        """Determine the outcome of this step.

        Automatic steps ignore player_input.
        Interactive steps read from player_input.
        """
        pass

    def apply(self) -> None:
        """Apply the resolved outcome to the character and set `self.outcome`."""
        pass

    def complete(self) -> None:
        """Mark this step as completed."""
        self.completed = True


class PassFailRollStep(Step):
    """A 2d6 + DM vs target check.

    Subclasses declare `step_id`, `check_label`, `status_pass`, `status_fail`,
    and pass the check characteristic + target into `super().__init__`.
    Subclasses may override `apply()` for side effects (e.g. promotion),
    but should still populate `self.outcome` with a matching shape.
    """

    step_type = StepType.AUTOMATIC
    check_label: str = "Check"
    status_pass: str = "PASSED"
    status_fail: str = "FAILED"

    def __init__(
        self,
        character: Character,
        check_characteristic: str,
        target: int,
    ) -> None:
        super().__init__(character)
        self.check_characteristic = check_characteristic
        self.target = target
        self.modifier: int = character.characteristics[
            check_characteristic
        ].modifier()

    def resolve(self, player_input: dict | None = None) -> None:
        self.raw_roll: int = roll(2)
        self.total_roll: int = self.raw_roll + self.modifier

    def apply(self) -> None:
        status = (
            self.status_pass
            if self.total_roll >= self.target
            else self.status_fail
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
            },
        )

    def _post_description(self, status: str) -> str:
        return (
            f"{self.check_label} check on {self.check_characteristic}: "
            f"rolled {self.total_roll} vs target {self.target} — {status}."
        )

    def prompt(self) -> StepPrompt:
        if self.outcome is not None:
            description = self.outcome.description
        else:
            description = (
                f"{self.check_label} check: 2d6 + {self.modifier} DM on "
                f"{self.check_characteristic} vs {self.target}."
            )
        return StepPrompt(
            step_id=self.step_id,
            step_type=self.step_type,
            description=description,
        )


class Term:
    """Base class for a life path term (a phase of character creation).

    A term holds a reference to a character and sequences one or more steps.
    Subclasses should populate self.steps in __init__ and override
    `next_term(session)` to drive the transition to the next term.
    """

    def __init__(self, character: Character) -> None:
        self.character: Character = character
        self.steps: list[Step] = []
        self.current_step_index: int = 0
        self.outcome: StepOutcome | None = None

    def label(self) -> str:
        """Human-readable label for this term, used to group step history."""
        return type(self).__name__

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

    def next_term(self, session: "GameSession") -> "Term | None":
        """Return the term that should run after this one completes, or None if done.

        The session is passed so terms can read/update session-level state
        (current career data, running term count, …). Default is no next term.
        """
        return None
