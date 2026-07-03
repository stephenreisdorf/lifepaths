# Extract the best-of-options qualification helper

`CareerTerm` and `AssignmentChangeTerm` contain the identical block that picks the qualification option giving the character the highest DM. Extracting it to a pure function removes the duplication and makes the selection testable in isolation.

## Problem

- The same ~6-line `max(qualification_options, key=lambda ...)` computation appears in `CareerTerm.__init__` (`src/terms/careers/terms.py:242-249`) and `AssignmentChangeTerm.__init__` (`src/terms/careers/terms.py:613-619`).
- Both hand-inline the `character.characteristics[...].modifier()` lookup with the same `-99` sentinel for a missing characteristic. A change to the tie-break or missing-stat handling must be made in both.

## Opportunity

Extract a pure function — e.g. `best_qualification_option(character, options) -> tuple[str, int]` returning `(characteristic, target)` — and call it from both constructors. Natural home is `src/terms/careers/terms.py` (module-level) or alongside the other parsers in `src/terms/careers/parsers.py`.

## Done when

- [ ] A single `best_qualification_option(...)` helper exists and both `CareerTerm` and `AssignmentChangeTerm` call it instead of inlining the `max(...)` block.
- [ ] A focused unit test covers the helper: highest-DM option wins, and a missing characteristic is ranked last.
- [ ] `uv run pytest` passes.

## Notes

Small, self-contained DRY cleanup. Independent of the other review items.
