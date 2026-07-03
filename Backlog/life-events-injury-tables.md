# Life Events and Injury tables are treated as flavor text only

Events and mishaps that instruct "Roll on the Life Events table" or "Roll on the
Injury table" currently resolve to plain flavor text with no mechanical effect.
The required sub-table rolls — and, for injuries, the specific characteristic
losses — never happen, so a chunk of the official consequence system is missing.

## Problem

`src/terms/effects.py` supports a fixed effect vocabulary (`skill`,
`characteristic`, `associate`, `forced_exit`, `enter_career`, and flavor-only
`advancement_dm` / `benefit_dm`). There is no `life_event` or `injury` effect and
no Life Events / Injury sub-tables. Career YAML entries such as Army event 7
("Life Event. Roll on the Life Events table.") and mishap 1/6 ("Roll on the
Injury table") therefore carry no mechanics.

Per Core Rulebook.pdf (Mongoose Traveller 2022), both are real 2D/1D sub-tables:
Life Events can grant/cost characteristics, skills, associates, and more; the
Injury table reduces physical characteristics by graded amounts.

Identified by a NotebookLM audit against Core Rulebook.pdf.

## Scope

- Add shared Life Events and Injury tables (a data file under `data/`, or a module
  alongside `src/terms/effects.py`) transcribed from the rulebook.
- Extend the effects vocabulary with `life_event` / `injury` effect types (or a
  generic "roll on named sub-table" effect) so YAML entries can trigger them, and
  wire resolution through `apply_effects`.
- Update the affected career YAML entries to use the new effect(s).
- Injury results feed existing `characteristic` reductions; reuse the death/0-floor
  handling already in the domain layer.

## Done when

- [ ] An event/mishap entry that rolls on the Life Events / Injury table applies a
      real mechanical result (characteristic/skill/associate change) rather than
      flavor-only text.
- [ ] The Life Events and Injury tables are transcribed and unit-tested with seeded
      dice (`src.utilities.rng`).
- [ ] At least the entries that reference these tables in existing career YAML are
      migrated to the new effect type.
- [ ] `uv run pytest` is green.

## Notes

Larger feature than the numeric-fidelity fixes; touches the effects layer and data
files. Independent of the education/aging/muster items. Related omission:
[Anagathics](anagathics.md).
</content>
