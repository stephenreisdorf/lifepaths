# Refactor: Career Step Sequencing Machine

`CareerTerm.advance()` in `src/terms/careers.py` is a 160+ line if-elif chain that checks `isinstance` against every Step type to decide what step comes next. It is the single coupling point for all step sequencing — every new step type or flow change requires editing this one method.

## Problem

- The method is hard to test in isolation. You must construct a full `CareerTerm` with real career data and step through the entire sequence to verify any single transition.
- Adding a new step type (e.g., a promotion skill roll) means modifying the monolithic `advance()` method rather than declaring the transition alongside the step.
- The step classes themselves are clean and independent, but the wiring between them is all in one place.

## Opportunity

Extract the sequencing logic into a declarative or pure-function form so that individual transitions can be tested independently and new steps can be added without editing the central method. Options include:

- A transition table mapping `(step_type, outcome)` → next steps
- A pure function `compute_next_steps(current_step, outcome, context) -> list[Step]`
- A pipeline/chain pattern where each step declares its own successor logic

## Scope

- `CareerTerm.advance()` (~160 lines)
- All 16 Step subclasses in `src/terms/careers.py` (as transition sources)
- `TransitionTerm.next_term()` (cross-term routing, similar pattern)
