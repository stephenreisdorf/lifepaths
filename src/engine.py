from src.character import Character
from src.terms.base import StepPrompt, StepType, SubmitResult
from src.terms.childhood import ChildhoodTerm


class GameSession:
    """Owns a character and its current term, driving the step lifecycle.

    The engine auto-advances through automatic steps so callers only
    interact when player input is needed.
    """

    def __init__(self) -> None:
        self.character = Character(name="Traveller", characteristics={}, skills={})
        self.term = ChildhoodTerm(self.character)

    def _character_summary(self) -> dict:
        """Serialize current character state for API responses."""
        return {
            "characteristics": {
                name: {"value": c.value, "modifier": c.modifier()}
                for name, c in self.character.characteristics.items()
            },
            "skills": list(self.character.skills.keys()),
        }

    def _auto_advance(self) -> tuple[list[StepPrompt], StepPrompt | None]:
        """Resolve consecutive automatic steps, return their prompts and the next interactive prompt."""
        resolved: list[StepPrompt] = []
        prompt = self.term.current_step_prompt()
        while prompt and prompt.step_type == StepType.AUTOMATIC:
            self.term.submit()  # resolve + apply + advance (no player input)
            # Re-read the prompt after resolution so it includes result data
            step = self.term.steps[self.term.current_step_index - 1]
            resolved.append(step.prompt())
            prompt = self.term.current_step_prompt()
        return resolved, prompt

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
