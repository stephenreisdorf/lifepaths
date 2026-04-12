# Skill table "+N" entries are added as skills, not characteristic bumps

`RollForSkillStep` in `src/terms/careers.py:152-153` applies the raw table entry via `increment_skill`, so entries like `Dexterity +1` from the Personal Development table end up as a skill named `"Dexterity +1"` instead of bumping the Dexterity characteristic. The site already carries a `specialty="TODO"` placeholder.

## Fix

Parse `"<Name> +<N>"` entries and route to `add_characteristic` when the name matches a known characteristic (see `AdvancementRollStep._apply_bonus` in `src/terms/careers.py:327-336` for the same parsing logic — extract into a shared helper).
