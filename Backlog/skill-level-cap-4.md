# Enforce skill-level cap of 4 during creation

Per the rules: "A skill may never exceed level 4 during Traveller creation."

Neither `Character.increment_skill` (`src/character.py:72-80`) nor `AdvancementRollStep._apply_bonus` (`src/terms/careers.py:327-336`) checks this.

## Fix

Cap skill/specialty rank at 4 in `Character.increment_skill`. Decide what happens when a rank would be raised beyond 4: silently clamp, or surface a player choice to apply it elsewhere (RAW typically says wasted).
