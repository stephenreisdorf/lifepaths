# Replace stringly-typed step statuses with a StepStatus enum

`StepOutcome.status` is a bare string that is produced as a literal in one place and branched on as a literal in another. Introducing a `StepStatus` enum removes the magic strings and the silent-fall-through failure mode when a producer and consumer drift.

## Problem

- `next_term()` branches on bare string literals — `"FAILED_QUAL"`, `"MISHAP"`, `"COMPLETED"`, `"FORCED_EXIT"`, `"FORCED_STAY"` (`src/terms/careers/terms.py:514-585`) — that are produced as unrelated literals elsewhere (e.g. `StepOutcome(status="MISHAP", ...)` at `src/terms/careers/terms.py:439`, and across the step classes in `src/terms/careers/steps.py`).
- Producer and consumer share no definition. A typo on either side fails silently: an unmatched status falls through to `return None`, quietly ending character creation with no error.
- `StepType` is already an enum in `src/terms/base.py`; `status` deserves the same treatment for the same reasons.

## Opportunity

Add a `StepStatus` enum (or a set of module-level constants) to `src/terms/base.py` and reference it on both the producing and consuming sides. Touches:

- `src/terms/base.py` — define the enum; `StepOutcome.status` typed against it (keep `str` compatibility via `str, Enum` so API serialization is unchanged).
- `src/terms/careers/steps.py`, `src/terms/careers/terms.py`, `src/terms/careers/muster_out.py`, `src/terms/education/steps.py`, `src/terms/education/terms.py` — replace literals with enum members.

## Done when

- [ ] `StepStatus` (a `str, Enum`) exists in `src/terms/base.py` and every status literal in the term/step flow references a member, not a raw string.
- [ ] `uv run pytest` passes with no changes to API response shapes (status still serializes to the same string values).
- [ ] `grep -rn '"FAILED_QUAL"\|"MISHAP"\|"FORCED_EXIT"\|"FORCED_STAY"\|"COMPLETED"' src/` returns only the enum definition.

## Notes

Highest-value item of the five from the architecture review — the only one that closes a latent silent-failure bug. `StepStatus` must stay `str`-compatible because `StepOutcome.status` and `StepPrompt.data["status"]` are serialized straight to the API (`src/engine.py:99`). No ordering dependency on the other review items.
