# Refactor: Engine Session State Sprawl

`GameSession` in `src/engine.py` accumulates cross-term state as a bag of mutable flags (`current_career_data`, `career_term_count`, `blocked_career`, `current_assignment`, `draft_used`). Terms reach into the session to read and write these fields via `session.*`, making dependencies between terms implicit and hard to test.

## Problem

- To test a `TransitionTerm` or `CareerTerm`, you must construct a `GameSession` with the right flags set. The required state is not documented — you discover it by reading the term code.
- Multiple terms mutate the same session fields, making it hard to reason about what state a term expects vs. what it produces.
- Adding new cross-term state means adding another field to `GameSession` and hoping all terms that need it remember to read/write it.

## Opportunity

Introduce a typed "career context" object that is passed explicitly to terms rather than accessed via the session:

- Makes the dependencies visible: a term declares what context it needs.
- Makes testing straightforward: construct the context object, pass it in, assert on the output.
- Reduces coupling between the engine and the domain layer — the engine manages the context lifecycle, terms consume and produce it.

## Scope

- `src/engine.py`: `GameSession` fields and `_next_term()` / `_auto_advance()`
- `src/terms/careers.py`: all `session.*` references in `CareerTerm`, `TransitionTerm`, `AssignmentChangeTerm`
