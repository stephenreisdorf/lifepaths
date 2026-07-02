# Refactor: Split the 2042-line careers.py Mega-Module

`src/terms/careers.py` contains 16 Step classes, 4 Term classes, utility parsers, muster-out logic, and aging logic — all in a single file. These are logically distinct concerns co-located by history, not necessity.

## Problem

- At 2042 lines, the file is difficult to navigate and reason about.
- Unrelated changes (e.g., fixing aging vs. fixing muster-out) touch the same file, increasing merge conflict risk.
- It's hard to write focused tests when everything is in one module.

## Opportunity

Split into focused sub-modules under `src/terms/careers/`:

- `steps.py` — the 16 Step subclasses (independent of each other)
- `terms.py` — `CareerTerm`, `TransitionTerm`, `AssignmentChangeTerm`
- `muster_out.py` — `MusterOutTerm` and benefit roll logic
- `aging.py` — `AgingStep` and age-bracket deterioration
- `parsers.py` — `parse_skill_entry()`, `try_apply_characteristic_bonus()`

## Notes

The Step subclasses are independent of each other but share imports from `base.py` and `character.py`. The split is organizational — no interface changes needed, just file boundaries.
