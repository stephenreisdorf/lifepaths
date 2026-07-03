# Convert CareerTerm.next_term if/elif to a status dispatch table

`CareerTerm.next_term` switches on `StepStatus` with a six-branch if/elif chain, while everything adjacent (`_STEP_HANDLERS`, `TransitionTerm._NEXT_TERM_HANDLERS`) uses declarative dispatch tables. Aligning it with the codebase's own convention makes the terminal-routing logic consistent and each branch independently testable.

## Problem

`src/terms/careers/terms.py:590-672` is a long `if status == ...` chain over `StepStatus.ANAGATHICS_PRISONER / FAILED_QUAL / MISHAP / COMPLETED / FORCED_EXIT / FORCED_STAY`. This is the one spot that breaks the dispatch-table convention the codebase otherwise holds (see `CareerTerm._STEP_HANDLERS` and `TransitionTerm._NEXT_TERM_HANDLERS`). Additionally, the "reset context for career exit" trio — `career_term_count = 0; blocked_career = ...; current_assignment = None` — is repeated across three branches.

## Opportunity

- Replace the if/elif with a `_TERMINAL_HANDLERS: dict[StepStatus, Callable]` mapping each terminal status to a small `_next_on_<status>` handler, matching the `advance()` dispatch style already used in the same class.
- Extract the repeated context reset into a helper (e.g. `CareerContext.reset_for_career_exit()` in `src/terms/context.py`).

## Done when

- [ ] `CareerTerm.next_term` resolves the next term via a status→handler table rather than an if/elif chain.
- [ ] The repeated `career_term_count/blocked_career/current_assignment` reset is a single named helper.
- [ ] Existing transition tests (`tests/test_career_transitions.py`) pass unchanged.
- [ ] `uv run pytest` passes.

## Notes

Consistency refactor, no behavior change. Pairs with [single-choice-step-base](single-choice-step-base.md) as a "match your own established patterns" cleanup. `AssignmentChangeTerm.next_term` has only two branches and can be left as-is or converted for symmetry. Keep `CLAUDE.md` / `AGENTS.md` career-flow notes accurate if the description of `next_term` changes.
