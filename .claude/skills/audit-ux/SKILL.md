---
name: audit-ux
description: Audit the lifepaths Vue frontend for UX and consistency problems (loading/error/disabled states, double-submit guards, accessibility, unrendered character-sheet fields, progress indication) and file each as a backlog candidate. One of the five focus audits behind `/audit ultimate`; also runnable standalone. Args: none (files to Backlog/) | "--candidates <output-file>" (coordinated mode).
---

# Audit — UX & frontend consistency

Sweeps the Vue 3 + Vite frontend for user-facing gaps and inconsistencies.

**Output & argument handling:** follow `../audit/output-modes.md`. No arg → file to `Backlog/` (no
commit). `--candidates <output-file>` → append candidate blocks only. Read `Backlog/README.md`'s
`## UX` section and `Backlog/done/` first — several UX items are already open (loading states,
network errors, accessibility, sheet fields, progress indicator, start-over confirmation); extend or
sharpen rather than duplicate them.

## Scope & sources

- **Code under audit:** `frontend/src/` — `App.vue` and every component (e.g. `CharacterCanvas.vue`),
  plus the fetch flows to `/api/start` and `/api/submit`.
- **Reference:** the backend `SubmitResult` / `StepPrompt` contract (`src/terms/base.py`) — the
  frontend is supposed to render any step generically and show both pre- and post-resolve prompts.
  Fields that cross the wire but never render are a real gap.

## What to look for

- **Async states:** every `fetch` should have a pending/disabled state; buttons must guard against
  double-submit; busy flags cleared in `finally`.
- **Error handling:** `res.ok` checked on *both* start and submit paths; `try/catch` around fetch and
  `res.json()`; a user-visible error channel on the welcome screen as well as mid-run.
- **Sheet completeness:** data on the wire (cash, possessions, associates, career records, etc.) that
  the finished sheet never renders. Confirm against the serialized character payload.
- **Progress & orientation:** phase stepper / term counter so the player knows where they are in the
  lifepath.
- **Accessibility:** color-only pass/fail signals, missing `aria-pressed` on selectable choices, no
  focus management across steps, unlabeled controls.
- **Destructive actions:** confirmation before "Start Over" or anything that discards a completed
  character.
- **Consistency:** repeated ad-hoc styling/markup that should be a shared component; dev-only affordances
  (raw JSON toggles) leaking into the finished experience.

## Recording a finding

Home category: **UX**. Framing: `## Opportunity`. Cite `frontend/src/...:line`. `## Done when` is an
observable behavior a person can verify (e.g. "a 500 from the backend shows a readable message, not a
frozen screen"). Frontend-only items don't need the pytest line. In `## Notes`, cross-link related
open UX items where the work pairs up.
