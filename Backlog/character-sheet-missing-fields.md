# Character sheet never shows cash, possessions, or associates

The `/api/start` + `/api/submit` payload includes `cash`, `possessions`, and `associates` (contacts/allies/rivals/enemies), but the frontend renders none of them. The finished character sheet — the payoff of the entire lifepath — silently drops three of the character's most important attributes.

## Problem

`src/engine.py:44-54` serializes `associates`, `cash`, and `possessions` into every response. A grep of `frontend/src` for `associate`, `cash`, `possession` returns nothing — `CharacterCanvas.vue` (the only place character state is rendered, reused by both `CreationScreen` and `CharacterSheet`) shows only characteristics, skills, and step history. Money earned, gear acquired, and the enemies/allies made across a career vanish from view.

## Opportunity

- Add canvas sections for **Cash & Possessions** and **Associates** (grouped by `AssociateType`: contact / ally / rival / enemy, with the `description` and `source_event`).
- These are especially important on the final `CharacterSheet`, where they complete the record.

## Done when

- [ ] Cash and possessions render in the character view.
- [ ] Associates render, grouped or labelled by type, including their description/source.
- [ ] Empty states are handled (no associates yet, zero possessions).

## Notes

Pure frontend — the data is already on the wire. Consider whether careers/terms-served/ranks should also surface (those are *not* currently in the summary; that would need an engine change — see [[character-read-model]]).
