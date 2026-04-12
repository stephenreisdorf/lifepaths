# Natural 12 on advancement forces the character to stay

Per the rules: "A natural 12 forces you to stay; you are too valuable to lose."

`AdvancementRollStep` (`src/terms/careers.py:302-303`) computes `self.advancement_roll: int = roll(2) + self.advancement_modifier` and never tracks the raw 2d6 result. `ContinueOrMusterOutStep` is always offered (`src/engine.py:97-101`).

## Fix

- Track the raw 2d6 total separately from the modified total in `AdvancementRollStep`.
- If raw == 12, flag the term so `_next_term` skips `ContinueOrMusterOutStep` and goes straight to the next `CareerTerm` in the same career.
