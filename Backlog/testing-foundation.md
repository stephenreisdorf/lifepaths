# Testing Foundation: pytest + Seedable RNG

The project has no test harness, and `utilities.roll()` calls the global `random` module directly (the one "rough edge" noted in CLAUDE.md). Together these make step and term logic untestable without monkeypatching. Nearly every architecture item in this backlog cites "hard to test in isolation" as its core problem — but none can deliver that payoff until there is something to test with and a way to make dice rolls deterministic.

This is the unstated prerequisite for the other refactors. It is small and unblocks all of them.

## Problem

- No test runner, no test directory, no fixtures. Verifying any change means manually stepping through character creation via the API or frontend.
- `roll(d)` in `src/utilities.py` uses module-global `random`, so any logic that rolls dice produces non-deterministic results. Tests cannot assert on outcomes without seeding or patching.
- Each refactor (typed data model, sequencing machine, session state, skill-grant consolidation) wants to assert behavior in isolation, but there is no foundation to do so.

## Opportunity

Establish a minimal, deterministic testing setup:

- Add `pytest` as a dev dependency (`uv add --dev pytest`) and a `tests/` directory.
- Make dice rolls deterministic in tests — either seed the global RNG in a fixture, or refactor `roll()` to accept/inject an RNG (e.g., a module-level `random.Random` instance that tests can seed or replace). Injecting is cleaner and removes the global-state rough edge for good.
- Add a couple of seed tests to prove the harness works: e.g., `Character.modifier()` arithmetic, `grant_skill()` budget/level caps, and one full deterministic run through `ChildhoodTerm`.
- Document `uv run pytest` in CLAUDE.md / AGENTS.md (both currently say "No tests or linter are configured yet").

## Scope

- `pyproject.toml` — add pytest dev dependency.
- `src/utilities.py` — make `roll()` seedable/injectable.
- `tests/` — new directory with initial test modules and any shared fixtures (e.g., seeded RNG, sample career data).
- `CLAUDE.md` / `AGENTS.md` — replace the "no tests configured" note with the test command.

## Notes

Recommended to land before [Typed career data model](typed-career-data-model.md) and the larger control-flow refactors ([Career step sequencing machine](career-step-sequencing-machine.md), [Engine session state](engine-session-state.md)), so those refactors can be verified rather than hand-checked.
