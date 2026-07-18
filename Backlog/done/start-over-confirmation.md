# "Start Over" discards a finished character with no confirmation

On the final character sheet, the "Start Over" button immediately wipes the completed character and begins a new lifepath. A single misclick destroys the whole result of the run with no undo.

## Problem

`frontend/src/components/CharacterSheet.vue:21` emits `restart`, which `App.vue:114` binds straight to `startCreation()` — a fresh `POST /api/start` that overwrites `characterData`, `stepHistory`, and `sessionId`. There is no confirmation step and no way back to the character you just built.

## Opportunity

- Prompt for confirmation before discarding a completed character.
- Or make the finished sheet non-destructive: keep it viewable and let "Start Over" open a new run without clobbering the last.

## Done when

- [ ] Restarting from a finished sheet requires an explicit confirmation.
- [ ] A single accidental click cannot silently destroy a completed character.

## Notes

Frontend only. Small. Related to giving the finished sheet a proper home — see [[final-sheet-presentation]].
