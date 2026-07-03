# Pull the advance() dispatch boilerplate up into a DispatchTerm base

Four terms hand-roll the identical `advance()` body that dispatches the just-resolved step through a `_STEP_HANDLERS` table. Extracting the mechanism into a shared base leaves each term declaring only its table.

## Problem

- The dispatch body is copy-pasted 4× — `src/terms/careers/terms.py:478-492` (`CareerTerm`), `:674-681` (`AssignmentChangeTerm`), and `src/terms/education/terms.py:142` & `:229` (the two education terms):

  ```python
  def advance(self):
      step = self.current_step
      super().advance()
      if step is None or step.outcome is None:
          return
      handler = self._STEP_HANDLERS.get(type(step))
      if handler is not None:
          handler(self, step)
  ```

- The four copies must stay in lockstep; a fix to the dispatch mechanics (e.g. handling a missing handler) has to be made in four places.

## Opportunity

Introduce a `DispatchTerm(Term)` base in `src/terms/base.py` that defines `advance()` once and reads a subclass-provided `_STEP_HANDLERS` class attribute (Template Method). `CareerTerm`, `AssignmentChangeTerm`, and both education terms then subclass `DispatchTerm` and declare only their `_STEP_HANDLERS` table, deleting their `advance()` overrides.

## Done when

- [ ] `DispatchTerm` exists in `src/terms/base.py` with the single `advance()` implementation.
- [ ] `CareerTerm`, `AssignmentChangeTerm`, and both `src/terms/education/terms.py` terms extend `DispatchTerm` and no longer define their own `advance()`.
- [ ] `grep -rn "self._STEP_HANDLERS.get" src/terms/` returns exactly one hit (the base).
- [ ] `uv run pytest` passes (notably `tests/test_career_transitions.py`).

## Notes

Purely organizational — no behavior change. `TransitionTerm` uses a different `_NEXT_TERM_HANDLERS` mechanism (dispatched in `next_term`, not `advance`) and is out of scope. No ordering dependency on the other review items, but pairs naturally with the status-enum work since both touch the term flow.
