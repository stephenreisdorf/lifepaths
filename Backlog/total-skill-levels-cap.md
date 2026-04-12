# Enforce total-skill-levels cap of 3 × (INT + EDU)

Per the rules: "A Traveller may never have more total skill levels than 3 × (INT + EDU)."

Not enforced anywhere in the codebase.

## Fix

- Add a helper on `Character` that sums all `base_rank` + specialty ranks.
- On any skill increment, compare against `3 * (INT.value + EDU.value)` and refuse if it would exceed.
- Decide how to surface the refusal to the player (silent clamp on auto-rolls? Force re-roll? Show a warning and waste the grant?).
