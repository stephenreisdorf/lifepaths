from src.character import Character
from src.character_summary import CharacterSummary
from src.terms.base import (
    LifepathPhase,
    LifepathProgress,
    StepPrompt,
    StepType,
    SubmitResult,
    Term,
)
from src.terms.childhood import ChildhoodTerm
from src.terms.context import CareerContext


class GameSession:
    """Owns a character and its current term, driving the step lifecycle.

    Every step — automatic or choice — requires an explicit submit so the
    frontend can display pre-resolve prompts and post-resolve outcomes.
    Term-to-term transitions remain automatic: when a term is exhausted
    the engine advances into the next term so the frontend never sees an
    empty state between terms.
    """

    def __init__(self, *, anagathics_enabled: bool = False) -> None:
        self.character = Character(name="Traveller", characteristics={}, skills={})
        self.term: Term = ChildhoodTerm(self.character)
        # Cross-term creation state lives in a typed context object that is
        # passed explicitly to each term's next_term(). The engine owns the
        # context's lifecycle; terms read and mutate its fields.
        self.context = CareerContext(
            character=self.character, anagathics_enabled=anagathics_enabled
        )

    def _character_summary(self) -> dict:
        """Serialize current character state for API responses.

        Delegates to the `CharacterSummary` read model so the engine stays out
        of the domain models' internals; see src/character_summary.py.
        """
        return CharacterSummary.from_character(self.character).model_dump()

    def _progress(self) -> LifepathProgress:
        """Describe the current position in the four-phase creation arc."""
        from src.terms.careers.muster_out import MusterOutTerm
        from src.terms.education import (
            MilitaryAcademyTerm,
            PreCareerChoiceTerm,
            UniversityTerm,
        )

        if isinstance(self.term, ChildhoodTerm):
            phase = LifepathPhase.CHILDHOOD
            phase_index = 1
        elif isinstance(
            self.term,
            (PreCareerChoiceTerm, UniversityTerm, MilitaryAcademyTerm),
        ):
            phase = LifepathPhase.EDUCATION
            phase_index = 2
        elif isinstance(self.term, MusterOutTerm):
            phase = LifepathPhase.MUSTER_OUT
            phase_index = 4
        else:
            phase = LifepathPhase.CAREER
            phase_index = 3

        career_term_number = None
        if phase == LifepathPhase.CAREER:
            career_term_number = getattr(self.term, "term_number", None)
            if career_term_number is None and self.context.career_term_count:
                career_term_number = self.context.career_term_count

        return LifepathProgress(
            phase=phase,
            phase_index=phase_index,
            career_term_number=career_term_number,
        )

    def _advance_past_term_boundaries(self) -> StepPrompt | None:
        """Cross exhausted term boundaries until a step is available, or the chain ends."""
        prompt = self._current_prompt_with_label()
        if prompt is None:
            next_term = self.term.next_term(self.context)
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
            progress=self._progress(),
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
            progress=self._progress(),
        )
