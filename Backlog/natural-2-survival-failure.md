# Natural 2 on survival is always a failure

Per the rules: "A natural 2 is always a failure, regardless of modifiers."

`SurvivalCheckStep.apply()` (`src/terms/careers.py:190-194`) only compares total vs target; raw dice aren't preserved, so a natural 2 with a +3 DM currently passes a target of 5.

## Fix

Track the raw 2d6 total in `SurvivalCheckStep.resolve()` alongside the modified total, and fail if raw == 2 even if modified total ≥ target.
