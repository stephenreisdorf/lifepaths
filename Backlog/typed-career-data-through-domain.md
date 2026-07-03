# Keep CareerData typed through the domain layer instead of flattening to dicts

`CareerData` is a fully validated Pydantic model, but `CareerTerm` immediately converts it to plain dicts and passes loose `dict`s through the entire career flow. Retaining the typed shapes where they never cross the generic API contract would restore type safety and remove the `type: ignore` accesses.

## Problem

- `CareerTerm.__init__` flattens the typed model on construction — `assignments_as_dicts()`, `normalized_skill_tables()`, `qualification_options()` (`src/terms/careers/terms.py:218-232`) — and dicts then flow everywhere: `current_assignment: dict`, `qualification_options: list[dict]`, `outcome.data["assignment"]`, `outcome.data["skill_table"]`.
- The lost typing surfaces as stringly-keyed access (`["characteristic"]`, `["name"]`, `["target"]`) throughout `terms.py`/`steps.py`, and as `# type: ignore[attr-defined]` on `inner.career_name` in `TransitionTerm` (`src/terms/careers/terms.py:85-87,157,163`).
- Primitive-obsession ("Start with the Data"): the validated types built in `src/career_data.py` are discarded at the domain boundary.

## Opportunity

Keep the typed models (`Assignment`, `CharacteristicCheck`, `SkillTable`) as the internal state of `CareerTerm` / `AssignmentChangeTerm` where that state never crosses the API. Convert to plain dicts only at the actual serialization boundary (`StepPrompt.data` / `StepOutcome.data`, which are intentionally loose `dict` for the generic frontend contract). Removing the `# type: ignore` accesses — e.g. via a small typed carrier or a Protocol for the decision steps that expose `career_name` — is part of the same cleanup.

## Done when

- [ ] `CareerTerm` and `AssignmentChangeTerm` hold assignments/qualification as typed models internally rather than `dict`, with dict conversion pushed to the `StepPrompt`/`StepOutcome` boundary.
- [ ] The `# type: ignore[attr-defined]` accesses on `inner.career_name` in `src/terms/careers/terms.py` are removed (via a declared attribute/Protocol on the decision steps).
- [ ] `uv run pytest` passes and API response shapes are unchanged.

## Notes

Largest and most judgment-dependent of the five review items — scope it carefully and consider doing it incrementally (assignments first, then qualification). Do **not** attempt to type the generic `StepPrompt.data` / `StepOutcome.data` payloads; their looseness is deliberate for the self-describing API. Best sequenced **after** the status-enum ([status-string-enum](status-string-enum.md)) and DispatchTerm ([dispatch-term-base](dispatch-term-base.md)) items land, since all three touch the same term flow and the smaller two reduce churn first.
