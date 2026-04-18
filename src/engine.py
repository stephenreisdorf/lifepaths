from src.character import Character
from src.terms.base import StepPrompt, StepType, SubmitResult, Term
from src.terms.childhood import ChildhoodTerm


class GameSession:
    """Owns a character and its current term, driving the step lifecycle.

    Every step — automatic or choice — requires an explicit submit so the
    frontend can display pre-resolve prompts and post-resolve outcomes.
    Term-to-term transitions remain automatic: when a term is exhausted
    the engine advances into the next term so the frontend never sees an
    empty state between terms.
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
            "age": self.character.age,
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

    def _advance_past_term_boundaries(self) -> StepPrompt | None:
        """Cross exhausted term boundaries until a step is available, or the chain ends."""
        prompt = self._current_prompt_with_label()
        if prompt is None:
            next_term = self.term.next_term(self)
            if next_term is not None:
                self.term = next_term
                return self._advance_past_term_boundaries()
        return prompt

    def _current_prompt_with_label(self) -> StepPrompt | None:
        """Return the current term's next prompt with the term label attached."""
        prompt = self.term.current_step_prompt()
        if prompt is not None:
            prompt.term_label = self.term.label()
        return prompt

    def start(self) -> SubmitResult:
        """Begin the session: return the first step's prompt, crossing any empty term boundaries."""
        next_prompt = self._advance_past_term_boundaries()
        return SubmitResult(
            resolved_steps=[],
            next_prompt=next_prompt,
            character=self._character_summary(),
        )

    def submit(self, player_input: dict | None = None) -> SubmitResult:
        """Submit the current step, then return the next prompt.

        For automatic steps, the just-resolved step's post-resolve prompt is
        returned in `resolved_steps` so the frontend can show the outcome
        before advancing. Choice steps leave `resolved_steps` empty — the
        frontend already tracks the player's selection locally.
        """
        submitted_step = self.term.current_step
        submitted_term_label = self.term.label()
        self.term.submit(player_input)

        resolved: list[StepPrompt] = []
        if submitted_step is not None and submitted_step.step_type == StepType.AUTOMATIC:
            step_prompt = submitted_step.prompt()
            step_prompt.term_label = submitted_term_label
            if submitted_step.outcome is not None:
                enriched = dict(submitted_step.outcome.data)
                enriched["status"] = submitted_step.outcome.status
                step_prompt.data = enriched
            resolved.append(step_prompt)

        next_prompt = self._advance_past_term_boundaries()
        return SubmitResult(
            resolved_steps=resolved,
            next_prompt=next_prompt,
            character=self._character_summary(),
        )
