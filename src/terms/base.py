from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Callable, ClassVar

from pydantic import BaseModel, Field

from src.character import Character
from src.utilities import roll

if TYPE_CHECKING:
    from src.terms.context import CareerContext


class StepType(str, Enum):
    """The kind of interaction a step requires."""

    AUTOMATIC = "automatic"  # No player input (e.g. dice roll)
    CHOICE = "choice"  # Player picks N items from a list


class StepStatus(str, Enum):
    """Machine-readable outcome tag produced by a step and branched on by terms.

    A `str, Enum` so members serialize to their string value unchanged (the API
    ships `outcome.status` straight through in `src/engine.py`) while giving
    producers and consumers a single shared definition. An unknown status now
    fails loudly at `StepOutcome` construction instead of silently falling
    through `next_term()` to `return None`.
    """

    # Generic / default
    DONE = "done"
    PASSED = "PASSED"
    FAILED = "FAILED"
    ROLLED = "ROLLED"
    SELECTED = "SELECTED"
    CHOSEN = "CHOSEN"
    SKIP = "SKIP"
    SKIPPED = "SKIPPED"

    # Pre-career education
    QUALIFIED = "QUALIFIED"
    NOT_ADMITTED = "NOT_ADMITTED"
    EDUCATED = "EDUCATED"
    GRADUATED = "GRADUATED"
    NOT_GRADUATED = "NOT_GRADUATED"
    ATTENDED = "ATTENDED"

    # Career term
    TRAINED = "TRAINED"
    SURVIVED = "SURVIVED"
    MISHAP = "MISHAP"
    EVENT = "EVENT"
    PROMOTED = "PROMOTED"
    NOT_PROMOTED = "NOT_PROMOTED"
    AT_MAX_RANK = "AT_MAX_RANK"
    COMMISSIONED = "COMMISSIONED"
    FAILED_COMMISSION = "FAILED_COMMISSION"

    # Career-term terminal outcomes (branched on by CareerTerm.next_term)
    FAILED_QUAL = "FAILED_QUAL"
    FORCED_EXIT = "FORCED_EXIT"
    FORCED_STAY = "FORCED_STAY"
    COMPLETED = "COMPLETED"

    # Transition / assignment-change choices
    CONTINUE = "CONTINUE"
    MUSTER_OUT = "MUSTER_OUT"
    CHANGE_ASSIGNMENT = "CHANGE_ASSIGNMENT"
    CHOOSE_CAREER = "CHOOSE_CAREER"
    DRAFTED = "DRAFTED"
    DRIFTER = "DRIFTER"
    CHANGED = "CHANGED"
    CHANGE_FAILED = "CHANGE_FAILED"

    # Muster-out
    CASH = "CASH"
    BENEFITS = "BENEFITS"
    MUSTERED_OUT = "MUSTERED_OUT"

    # Aging
    NO_AGING = "NO_AGING"
    AGED = "AGED"
    AGING_CRISIS = "AGING_CRISIS"

    # Anagathics (optional anti-aging rule; start-of-term)
    ANAGATHICS_STARTED = "ANAGATHICS_STARTED"
    ANAGATHICS_DECLINED = "ANAGATHICS_DECLINED"
    ANAGATHICS_MISSED = "ANAGATHICS_MISSED"
    ANAGATHICS_MAINTAINED = "ANAGATHICS_MAINTAINED"
    ANAGATHICS_PRISONER = "ANAGATHICS_PRISONER"


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

    `status` is a `StepStatus` member (e.g. QUALIFIED, FAILED, SURVIVED,
    MISHAP, CONTINUE, MUSTER_OUT) — a machine-readable tag terms branch on.
    `description` is the human-readable sentence rendered into the post-resolve
    prompt. `data` carries structured details (roll totals, selections, …).
    """

    status: StepStatus = StepStatus.DONE
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


class SingleChoiceStep(Step):
    """A choice step where the player must pick exactly one available option.

    Subclasses provide the current option labels and react to the selected
    value. This mirrors `PassFailRollStep`: the shared base owns the repeated
    lifecycle plumbing while concrete steps keep their domain-specific prompt
    and side effects.
    """

    step_type = StepType.CHOICE

    input_required_message: str = "Selection is required."
    single_choice_message: str = "Must choose a single option."

    def options(self) -> list[str]:
        """Return the currently available option labels."""
        raise NotImplementedError

    def resolve(self, player_input: dict | None = None) -> None:
        if player_input is None:
            raise ValueError(self.input_required_message)
        selections = player_input.get("selections", [])
        if len(selections) != 1:
            raise ValueError(self.single_choice_message)
        selection = selections[0]
        if selection not in self.options():
            raise ValueError(self.invalid_choice_message(selection))
        self.on_choice(selection)

    def invalid_choice_message(self, selection: str) -> str:
        return f"Unavailable option: {selection}"

    def on_choice(self, selection: str) -> None:
        """Handle the selected option after base validation passes."""
        raise NotImplementedError


class PassFailRollStep(Step):
    """A 2d6 + DM vs target check.

    Subclasses declare `step_id`, `check_label`, `status_pass`, `status_fail`,
    and pass the check characteristic + target into `super().__init__`.
    Subclasses may override `apply()` for side effects (e.g. promotion),
    but should still populate `self.outcome` with a matching shape.
    """

    step_type = StepType.AUTOMATIC
    check_label: str = "Check"
    status_pass: StepStatus = StepStatus.PASSED
    status_fail: StepStatus = StepStatus.FAILED

    def __init__(
        self,
        character: Character,
        check_characteristic: str,
        target: int,
        extra_dm: int = 0,
    ) -> None:
        super().__init__(character)
        self.check_characteristic = check_characteristic
        self.target = target
        # `extra_dm` folds in situational bonuses (e.g. a university
        # graduate's DM to their first career qualification) on top of the
        # characteristic modifier.
        self.extra_dm = extra_dm
        self.modifier: int = (
            character.characteristics[check_characteristic].modifier() + extra_dm
        )

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
            f"rolled {self.total_roll} vs target {self.target} — {status.value}."
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
    `next_term(context)` to drive the transition to the next term.
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

    def next_term(self, context: "CareerContext") -> "Term | None":
        """Return the term that should run after this one completes, or None if done.

        The career context is passed so terms can read/update cross-term
        creation state (current career data, running term count, …) via an
        explicit, typed object rather than the engine. Default is no next term.
        """
        return None


class DispatchTerm(Term):
    """A `Term` that dispatches each resolved step through a handler table.

    Subclasses declare a `_STEP_HANDLERS` mapping of step type → handler
    (an unbound method taking `(self, step)`) and nothing else about the
    dispatch mechanism. After the current step is completed, `advance()`
    looks up the just-resolved step's type and calls its handler, which
    dynamically appends the next step(s) or synthesizes a terminal outcome.

    This is the Template Method that `CareerTerm`, `AssignmentChangeTerm`,
    and the two education terms share instead of hand-rolling identical
    `advance()` bodies.
    """

    _STEP_HANDLERS: ClassVar[dict[type[Step], Callable[["DispatchTerm", Step], None]]] = {}

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
