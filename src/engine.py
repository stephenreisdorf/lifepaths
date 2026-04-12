from src.career_loader import career_to_term_kwargs, get_available_careers, load_career
from src.character import Character
from src.terms.base import StepPrompt, StepType, SubmitResult
from src.terms.careers import (
    CareerTerm,
    ChooseCareerStep,
    ContinueOrMusterOutStep,
    RollQualificationStep,
    TransitionTerm,
)
from src.terms.childhood import ChildhoodTerm


class GameSession:
    """Owns a character and its current term, driving the step lifecycle.

    The engine auto-advances through automatic steps so callers only
    interact when player input is needed.  When a term completes it
    determines the next term via _next_term(), transparently chaining
    childhood → career selection → career terms → muster out.
    """

    def __init__(self) -> None:
        self.character = Character(name="Traveller", characteristics={}, skills={})
        self.term = ChildhoodTerm(self.character)
        self.current_career_data: dict | None = None
        self.career_term_count: int = 0

    def _character_summary(self) -> dict:
        """Serialize current character state for API responses."""
        return {
            "characteristics": {
                name: {"value": c.value, "modifier": c.modifier()}
                for name, c in self.character.characteristics.items()
            },
            "skills": {
                name: {
                    "base_rank": s.base_rank,
                    "specialties": {
                        sp_name: sp.rank for sp_name, sp in s.specialties.items()
                    },
                }
                for name, s in self.character.skills.items()
            },
        }

    def _next_term(self):
        """Determine the next term after the current one finishes, or None if creation is done."""
        finished = self.term

        if isinstance(finished, ChildhoodTerm):
            careers = get_available_careers()
            return TransitionTerm(self.character, ChooseCareerStep(self.character, careers))

        if isinstance(finished, TransitionTerm):
            inner = finished.steps[0]

            if isinstance(inner, ChooseCareerStep):
                self.current_career_data = load_career(inner.selected_career)
                self.career_term_count = 0
                kwargs = career_to_term_kwargs(self.current_career_data, is_first_term=True)
                return CareerTerm(self.character, **kwargs)

            if isinstance(inner, ContinueOrMusterOutStep):
                if inner.decision == "Continue":
                    kwargs = career_to_term_kwargs(self.current_career_data, is_first_term=False)
                    return CareerTerm(self.character, **kwargs)
                return None  # Muster Out — creation is done

        if isinstance(finished, CareerTerm):
            # Check for qualification failure (term ended after only the qualification step)
            qual_step = finished.steps[0]
            if (
                isinstance(qual_step, RollQualificationStep)
                and hasattr(qual_step, "qualification_status")
                and qual_step.qualification_status == "FAILED"
            ):
                careers = get_available_careers()
                return TransitionTerm(
                    self.character, ChooseCareerStep(self.character, careers)
                )

            self.career_term_count += 1
            return TransitionTerm(
                self.character,
                ContinueOrMusterOutStep(self.character, finished.career_name),
            )

        return None

    def _auto_advance(self) -> tuple[list[StepPrompt], StepPrompt | None]:
        """Resolve consecutive automatic steps, return their prompts and the next interactive prompt."""
        resolved: list[StepPrompt] = []
        prompt = self._current_prompt_with_label()
        while prompt and prompt.step_type == StepType.AUTOMATIC:
            self.term.submit()  # resolve + apply + advance (no player input)
            # Re-read the prompt after resolution so it includes result data
            step = self.term.steps[self.term.current_step_index - 1]
            step_prompt = step.prompt()
            step_prompt.term_label = self.term.label()
            resolved.append(step_prompt)
            prompt = self._current_prompt_with_label()

        # If current term is exhausted, try to transition to the next term
        if prompt is None:
            next_term = self._next_term()
            if next_term is not None:
                self.term = next_term
                more_resolved, prompt = self._auto_advance()
                resolved.extend(more_resolved)

        return resolved, prompt

    def _current_prompt_with_label(self) -> StepPrompt | None:
        """Return the current term's next prompt with the term label attached."""
        prompt = self.term.current_step_prompt()
        if prompt is not None:
            prompt.term_label = self.term.label()
        return prompt

    def start(self) -> SubmitResult:
        """Begin the term: auto-resolve initial automatic steps and return the first interactive prompt."""
        resolved, next_prompt = self._auto_advance()
        return SubmitResult(
            resolved_steps=resolved,
            next_prompt=next_prompt,
            character=self._character_summary(),
        )

    def submit(self, player_input: dict | None = None) -> SubmitResult:
        """Submit player input for the current step, then auto-advance through any subsequent automatic steps."""
        self.term.submit(player_input)
        resolved, next_prompt = self._auto_advance()
        return SubmitResult(
            resolved_steps=resolved,
            next_prompt=next_prompt,
            character=self._character_summary(),
        )
