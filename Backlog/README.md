# Backlog

One file per open issue. Index below.

## Bugs

_(none)_

## UX

_(none)_

## Architecture

- [Inject a CareerRepository](career-repository-injection.md) — terms read careers through an injected repository instead of calling the filesystem loader on every transition; decouples + caches + makes transitions testable without disk.
- [SingleChoiceStep base](single-choice-step-base.md) — dedup the identical `resolve()` validation across ~8 choice steps behind a Template-Method base, mirroring `PassFailRollStep`.
- [CareerTerm.next_term dispatch table](career-term-next-term-dispatch.md) — replace the six-branch status if/elif with a `StepStatus`→handler table to match the codebase's own dispatch convention.
- [Keep Rank typed through steps](typed-rank-through-steps.md) — thread `list[Rank]` into the rank steps and factor one `apply_rank_bonus` helper instead of `list[dict]` + duplicated logic.
- [Character read model](character-read-model.md) — move `GameSession._character_summary` serialization onto the model / a read model so the engine stops reaching into every domain model's internals.
- [Typed career summary](typed-career-summary.md) — replace the loosely-typed career-summary dict with a `CareerSummary` model through eligibility + selection; best folded into the repository item.

## Deferred

- [Connections Rule (multi-character)](connections-rule.md) — shared events between two Travellers; requires multi-character session model. May be deferred indefinitely for single-player use.
