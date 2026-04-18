# Refactor: Consolidate Skill Grant API Surface

The "grant a skill" concept is split across three overlapping methods on `Character` (`add_skill`, `increment_skill`, `grant_skill`) plus a parallel implementation in `src/terms/effects.py` (`_apply_skill`). Callers must know which API to use, and a rule change (e.g., to the budget cap) must be verified in multiple places.

## Problem

- `grant_skill()` handles Traveller notation (bare name = +1, "Skill 0" = ensure exists, "Skill N" = set to max(current, N)).
- `increment_skill()` handles deltas with specialty support.
- `add_skill()` ensures a skill exists at rank 0.
- `effects._apply_skill()` reimplements parts of this logic for event/mishap effects.
- The budget cap (`3 × (INT + EDU)`) and level cap (4) are enforced in `Character._budget_allows_increment()`, but effects has its own path to character mutation.

## Opportunity

Consolidate to a single skill-mutation entry point on `Character` that all callers use. This would:

- Ensure budget cap, level cap, and specialty logic are tested and enforced in one place.
- Reduce the API surface callers need to understand.
- Let `effects.py` delegate to `Character` rather than reimplementing grant logic.

## Scope

- `src/character.py`: `add_skill()`, `increment_skill()`, `grant_skill()`, `_budget_allows_increment()`
- `src/terms/effects.py`: `_apply_skill()`
- All call sites across Step classes in `src/terms/careers.py` and `src/terms/childhood.py`
