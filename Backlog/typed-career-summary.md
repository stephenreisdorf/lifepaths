# Replace the loosely-typed career-summary dict with a typed model

`get_available_careers()` returns `list[dict]` summaries that float stringly-typed through eligibility filtering, career selection, and into `ChooseCareerStep`. A small `CareerSummary` model tightens that path and removes `.get("qualification")` / `career["name"]` dict spelunking.

## Problem

`src/career_loader.py:17` returns `qualification_summary()` dicts. They travel through `filter_eligible_careers` (`career_loader.py:26`, reading `career.get("entry_only")`, `qual.get("auto")`, `option["characteristic"]`), `_available_careers_for` / `_after_choose_career` (`src/terms/careers/terms.py`), and `ChooseCareerStep` (`src/terms/careers/steps.py`, `c["name"]`) — all by string key, with no validation once past the loader.

## Opportunity

- Add a `CareerSummary` Pydantic model (name, description, a typed qualification summary, `entry_only`) produced by `CareerData.qualification_summary()`.
- Thread it through `filter_eligible_careers`, `_available_careers_for`, and `ChooseCareerStep`, converting to a plain dict only at the `StepPrompt` / API boundary.

## Done when

- [ ] `get_available_careers()` (or its repository equivalent) returns typed `CareerSummary` objects.
- [ ] Eligibility filtering and `ChooseCareerStep` consume the typed summary, not raw dicts, up to the API boundary.
- [ ] `uv run pytest` passes.

## Notes

Minor "start with the data" cleanup; lowest priority of the set. Best done **as part of** [career-repository-injection](career-repository-injection.md) — if the repository returns typed summaries, this comes almost for free. Do not do it standalone if the repository work is imminent.
