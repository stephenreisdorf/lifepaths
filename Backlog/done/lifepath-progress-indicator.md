# No sense of progress or place in the lifepath

The flow chains Childhood → (optional Education) → Career Selection → Career Terms → Muster Out across many steps, but the player is never shown where they are in that arc or how far they've come. Each step shows only its own `term_label`.

## Problem

`CreationScreen.vue` renders one prompt at a time with a `term_label` badge, and `StepHistoryLog.vue` groups completed steps by term in the side canvas. There is no roadmap of the phases, no "Term N" counter, and no indication of how long a run typically lasts. A first-time player has no mental model of the process — it feels like an open-ended series of dialogs.

## Opportunity

- Add a lightweight phase/stepper header (Childhood · Education · Career · Muster Out) that highlights the current phase.
- Show a term counter (e.g. "Career Term 3") once the career loop begins.

## Done when

- [ ] The current phase of the lifepath is always visible.
- [ ] The player can tell roughly how far along they are (term count or phase progress).

## Notes

Frontend, but may want the engine/response to expose the current phase/term number explicitly rather than parsing `term_label`. Coordinate with [[character-read-model]] if a richer response shape is added.
