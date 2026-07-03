from __future__ import annotations

from dataclasses import dataclass

from src.career_data import CareerData
from src.character import Character


@dataclass
class CareerContext:
    """Cross-term state for the career-creation flow.

    Passed explicitly to each ``Term.next_term()`` so a term's dependencies
    on shared creation state are visible in the signature and can be tested
    without constructing a full ``GameSession``. The engine owns the
    lifecycle of this object; terms consume and mutate its fields.

    Fields mirror the state that previously lived as loose flags on
    ``GameSession``:

    - ``character`` — the Traveller being created (the subject every term acts on).
    - ``current_career_data`` — the career currently being served, if any.
    - ``career_term_count`` — completed terms in the current career.
    - ``blocked_career`` — a career that just ejected the character; blocks
      re-entry for exactly the immediately-following Career Selection prompt.
    - ``current_assignment`` — most-recently-selected assignment under the
      current career (used by the assignment-change flow).
    - ``draft_used`` — whether the once-per-life Draft fallback has been used.
    - ``pre_career_qualification_dm`` — one-shot DM a university graduate
      carries into their first career qualification roll; consumed (and reset)
      when that first Career Selection starts the career.
    """

    character: Character
    current_career_data: CareerData | None = None
    career_term_count: int = 0
    blocked_career: str | None = None
    current_assignment: dict | None = None
    draft_used: bool = False
    pre_career_qualification_dm: int = 0
