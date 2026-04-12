# terms_served is not incremented on mishap-ended terms

`record_career_term` is only called from `AdvancementRollStep.apply()` (`src/terms/careers.py:307`), which means a mishap-ended term never increments `terms_served`. Once the "advancement roll ≤ terms served forces exit" rule is implemented (`advancement-roll-forces-exit.md`), this undercounting will break the exit logic — though the practical impact on that specific rule is low because a mishap already ends the career anyway.

More importantly: benefit rolls are allotted per term served (rules reference). If mishap terms don't tick `terms_served`, muster-out benefits will be short.

## Fix

Move the `record_career_term` call to a place that runs for both survived and mishap'd terms — e.g. into `CareerTerm.advance()` at term completion, or into both `AdvancementRollStep.apply()` and `MishapRollStep.apply()`.
