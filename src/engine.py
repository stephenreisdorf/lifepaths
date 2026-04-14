from src.character import Character
from src.terms.base import StepPrompt, StepType, SubmitResult, Term
from src.terms.childhood import ChildhoodTerm


class GameSession:
    """Owns a character and its current term, driving the step lifecycle.

    The engine auto-advances through automatic steps so callers only
    interact when player input is needed. Term-to-term transitions are
    owned by each term via `Term.next_term(session)`.
    """

    def __init__(self) -> None:
        self.character = Character(name="Traveller", characteristics={}, skills={})
        self.term: Term = ChildhoodTerm(self.character)
        self.current_career_data: dict | None = None
        self.career_term_count: int = 0
        # Name of the career that was just left (mishap or forced exit);
        # blocks re-entry for exactly the immediately-following Career
        # Selection prompt.
        self.blocked_career: str | None = None
        # Most-recently-selected assignment under the current career.
        # Used by the assignment-change flow to preserve state.
        self.current_assignment: dict | None = None
        # Whether the Draft fallback has already been used (once-per-life).
        self.draft_used: bool = False

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
            "associates": [
                {
                    "name": a.name,
                    "type": a.type.value,
                    "description": a.description,
                    "source_event": a.source_event,
                }
                for a in self.character.associates
            ],
            "cash": self.character.cash,
            "possessions": list(self.character.possessions),
        }

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
            next_term = self.term.next_term(self)
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
