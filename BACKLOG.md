# Backlog

Items that need to be worked on.

## Character Builder Canvas

The career term has a few more steps:

1. Make **Survival** roll — fail means a Mishap
2. If survived, roll on **Events** table
3. Make **Advancement** roll (optional for Commission first)
4. Decide to continue or leave; collect **Benefits** on leaving

The navy.yaml file should already have data for these steps.

## Known issues

- **Skill table "+N" entries are added as skills, not characteristic bumps.** `RollForSkillStep` (in `src/terms/careers.py`) applies the raw table entry via `increment_skill`, so entries like `Dexterity +1` from the Personal Development table end up as a skill named `"Dexterity +1"` instead of bumping the Dexterity characteristic. The site already carries a `specialty="TODO"` placeholder. Fix should parse `"<Name> +<N>"` entries and route to `add_characteristic` when the name matches a known characteristic (see `AdvancementRollStep._apply_bonus` for the same parsing logic).
- **Career rank is uncapped.** `Character.promote` keeps incrementing `CareerRecord.rank` past the highest entry in the YAML `ranks` list. No crash (the bonus lookup just no-ops when there's no matching entry), but e.g. Navy has ranks 0–6 and a character can currently reach rank 11+. Cap at `max(r["rank"] for r in ranks)` in `AdvancementRollStep`, or prevent further advancement rolls once the character is at max rank.