# Backlog

One file per open issue. Index below.

## Bugs

_None open._

## UX

- [Character sheet missing fields](character-sheet-missing-fields.md) — cash, possessions, and associates are on the wire but never rendered; the finished sheet drops three of the character's key attributes.
- [Final sheet presentation](final-sheet-presentation.md) — the finished character reuses the compact creation side-panel and exposes a dev-only Raw JSON toggle; give it a real, exportable sheet.
- [Expose the anagathics option](expose-anagathics-option.md) — the anti-aging rule is implemented and honoured by `/api/start` but the welcome screen never lets a player enable it.
- [Lifepath progress indicator](lifepath-progress-indicator.md) — no phase stepper or term counter; the player has no sense of where they are in the run.
- [Async loading states](async-loading-states.md) — no pending/disabled state on fetches; the UI looks frozen on latency and a double-click can double-submit a step.
- [Network error handling](network-error-handling.md) — `startCreation` has no try/catch or `res.ok` check; a down/500 backend leaves a blank, frozen screen.
- [Frontend accessibility](frontend-accessibility.md) — color-only pass/fail status, no `aria-pressed` on skill selection, and no focus management across steps.
- [Start Over confirmation](start-over-confirmation.md) — the finished sheet's "Start Over" destroys the completed character with no confirmation.

## Architecture

- [Inject a CareerRepository](career-repository-injection.md) — terms read careers through an injected repository instead of calling the filesystem loader on every transition; decouples + caches + makes transitions testable without disk.
- [SingleChoiceStep base](single-choice-step-base.md) — dedup the identical `resolve()` validation across ~8 choice steps behind a Template-Method base, mirroring `PassFailRollStep`.
- [CareerTerm.next_term dispatch table](career-term-next-term-dispatch.md) — replace the six-branch status if/elif with a `StepStatus`→handler table to match the codebase's own dispatch convention.
- [Keep Rank typed through steps](typed-rank-through-steps.md) — thread `list[Rank]` into the rank steps and factor one `apply_rank_bonus` helper instead of `list[dict]` + duplicated logic.
- [Character read model](character-read-model.md) — move `GameSession._character_summary` serialization onto the model / a read model so the engine stops reaching into every domain model's internals.
- [Typed career summary](typed-career-summary.md) — replace the loosely-typed career-summary dict with a `CareerSummary` model through eligibility + selection; best folded into the repository item.

## Deferred

- [Connections Rule (multi-character)](connections-rule.md) — shared events between two Travellers; requires multi-character session model. May be deferred indefinitely for single-player use.
