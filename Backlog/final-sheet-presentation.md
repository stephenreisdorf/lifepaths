# Finished character sheet is a bare reuse of the compact creation canvas

The end of the whole lifepath — the finished character — is presented as a plain "Character Sheet" heading over the same small side-panel `CharacterCanvas` used during creation, plus a "Start Over" button. It reads like a debug panel, not the deliverable, and includes a developer-only Raw JSON toggle.

## Problem

`CharacterSheet.vue` renders `<h2>Character Sheet</h2>` + the shared `CharacterCanvas` (the compact `aside` from the creation flow) + a restart button — no dedicated layout, no emphasis, no way to keep the result. The `CharacterCanvas` also exposes a **"Raw JSON" toggle** (`CharacterCanvas.vue:39-44`) that dumps internal state; that's a dev affordance leaking into the finished player-facing sheet. There's no export/print/save of the completed character.

## Opportunity

- Give the finished character its own full-width, readable sheet layout (characteristics, skills, associates, cash/possessions — see [[character-sheet-missing-fields]]).
- Hide the Raw JSON toggle from the player-facing sheet (keep it behind a dev flag, or remove it from `CharacterSheet`).
- Offer an export/print/copy of the finished character.

## Done when

- [ ] The finished sheet has a dedicated layout distinct from the in-creation side panel.
- [ ] The Raw JSON debug toggle is not part of the normal player-facing finished sheet.
- [ ] The player can export/print/copy their completed character (at least one of these).

## Notes

Frontend. Builds on [[character-sheet-missing-fields]] (the fields to show) and [[start-over-confirmation]] (not destroying it by accident).
