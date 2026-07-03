# Characteristic DM is wrong for a score of 0

The characteristic dice-modifier formula produces −2 for a score of 0, but
Traveller's DM table assigns −3 to a 0. Every DM-driven roll (qualification,
survival, advancement, skill checks) is one point too generous for a character
with a 0 in the relevant characteristic.

## Problem

`Characteristic.modifier()` computes `value // 3 - 2` (`src/character.py:12`).
That matches the official table for scores 1–15+, but not the bottom rung:

| Score | `value // 3 - 2` | Core Rulebook DM |
|-------|------------------|------------------|
| 0     | **−2**           | **−3**           |
| 1–2   | −2               | −2               |
| 3–5   | −1               | −1               |
| 6–8   | 0                | 0                |
| 9–11  | +1               | +1               |
| 12–14 | +2               | +2               |
| 15+   | +3               | +3               |

A 0 characteristic is reachable during creation (aging reductions floor at 0,
and mishaps/events can subtract), so the bug is live, not theoretical.

Identified by a NotebookLM audit of the implemented rules against the Core
Rulebook.pdf (Mongoose Traveller 2022) — characteristic DM table.

## Scope

- `src/character.py` — `Characteristic.modifier()`. Special-case 0 → −3 (or
  switch to an explicit lookup / `max(-3, ...)`-style clamp that reproduces the
  full table). Keep the formula for all other values.

## Done when

- [ ] `Characteristic(name="X", value=0).modifier() == -3`.
- [ ] Scores 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15 still return −2, −2, −1, −1, 0,
      0, +1, +1, +2, +2, +3 respectively.
- [ ] A regression test in `tests/test_character.py` pins the full 0–15 table.
- [ ] `uv run pytest` is green.

## Notes

Smallest of the rules-fidelity fixes and fully self-contained. No dependency on
the other education/aging items. Confirm the −3-at-0 row against the copy of the
rulebook in use before landing (the value is edition-stable across Mongoose 1e/2e).
</content>
