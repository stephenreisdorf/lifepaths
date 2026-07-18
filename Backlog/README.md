# Backlog

One file per open issue. Index below.

## Order

Execution sequence — `iterate` always works the first entry. Regenerate with `/backlog sort`.

1. [Expose the anagathics option](expose-anagathics-option.md)
2. [Lifepath progress indicator](lifepath-progress-indicator.md)
3. [Frontend accessibility](frontend-accessibility.md)
4. [Final sheet presentation](final-sheet-presentation.md)
5. [Connections Rule (multi-character)](connections-rule.md)

## Bugs

_None open._

## UX

- [Final sheet presentation](final-sheet-presentation.md) — the finished character reuses the compact creation side-panel and exposes a dev-only Raw JSON toggle; give it a real, exportable sheet.
- [Expose the anagathics option](expose-anagathics-option.md) — the anti-aging rule is implemented and honoured by `/api/start` but the welcome screen never lets a player enable it.
- [Lifepath progress indicator](lifepath-progress-indicator.md) — no phase stepper or term counter; the player has no sense of where they are in the run.
- [Frontend accessibility](frontend-accessibility.md) — color-only pass/fail status, no `aria-pressed` on skill selection, and no focus management across steps.

## Architecture

_None open._

## Deferred

- [Connections Rule (multi-character)](connections-rule.md) — shared events between two Travellers; requires multi-character session model. May be deferred indefinitely for single-player use.
