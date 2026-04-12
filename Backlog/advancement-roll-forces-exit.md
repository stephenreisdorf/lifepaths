# Advancement roll ≤ terms served forces exit

Per the rules: "If your advancement roll ≤ the number of terms spent in this career, you cannot continue — you must leave this term."

`AdvancementRollStep.apply()` (`src/terms/careers.py:305-315`) ticks `terms_served` and promotes but never flags the character as unable to continue. The engine always shows `ContinueOrMusterOutStep` afterward (`src/engine.py:97-101`).

## Fix

After the advancement roll, compare raw `advancement_roll` (minus DM, or just the raw 2d6 total depending on RAW interpretation) to `terms_served`. If the roll ≤ terms served, flag the term as force-exit; `_next_term` should route to `ChooseCareerStep` instead of `ContinueOrMusterOutStep`.

Clarify RAW: some editions interpret this as raw 2d6; others as the modified total. Match whatever source the rules doc is citing.
