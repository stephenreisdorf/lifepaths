# Keep Rank typed through the step layer and dedup rank-bonus application

`CareerData` validates ranks into a typed `Rank` model, but `CareerTerm` immediately flattens them to `list[dict]` and the step layer reaches in stringly-typed (`r.get("rank")`, `r.get("title")`, `r.get("bonus_skill")`). Passing `list[Rank]` through and factoring one bonus-application helper restores type safety and removes duplicated logic.

## Problem

`src/career_data.py:99` defines a validated `Rank`, but `CareerTerm` (`src/terms/careers/terms.py`) calls `ranks_as_dicts()` / `officer_ranks_as_dicts()`, and `AdvancementRollStep` / `CommissionStep` (`src/terms/careers/steps.py`) then index dicts by string key. On top of that, `AdvancementRollStep._apply_rank_bonus` (`steps.py:598`) and `CommissionStep._apply_officer_rank_bonus` (`steps.py:739`) are the same algorithm twice: find the rank entry for `new_rank`, apply `bonus_skill` via `try_apply_characteristic_bonus` else `grant_skill`, return the title.

## Opportunity

- Thread `list[Rank]` (from `career.ranks` / `career.officer_ranks`) through `CareerTerm` into `AdvancementRollStep` / `CommissionStep` instead of the `*_as_dicts()` views.
- Extract one free function, e.g. `apply_rank_bonus(character, ranks: list[Rank], new_rank) -> str | None`, and call it from both steps.
- Retire `ranks_as_dicts()` / `officer_ranks_as_dicts()` if nothing else depends on them.

## Done when

- [ ] `AdvancementRollStep` and `CommissionStep` receive typed `Rank` objects, not `list[dict]`.
- [ ] A single `apply_rank_bonus` helper replaces both `_apply_rank_bonus` and `_apply_officer_rank_bonus`.
- [ ] No `.get("rank"|"title"|"bonus_skill")` string-key access to rank data remains in the step layer.
- [ ] `uv run pytest` passes (rank-bonus and commission behavior unchanged).

## Notes

"Start with the data" + DRY. Independent of the other items. Update the `career_data.py` architecture note in `CLAUDE.md` / `AGENTS.md` if the `*_as_dicts()` views are removed.
