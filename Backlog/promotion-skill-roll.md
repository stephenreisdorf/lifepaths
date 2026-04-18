# Promotion Should Grant a Bonus Skill Roll

When a character is promoted during a career term, they should receive an additional roll on a skill table as a reward. Currently, promotion updates rank but does not trigger an extra skill roll.

## Current behavior

`AdvancementRollStep` in `src/terms/careers.py` records the promotion on the character sheet but does not append a follow-up `ChooseCareerSkillsTable` + `RollForSkillStep` sequence for the bonus roll.

## Expected behavior

On successful advancement (promotion), the term should insert an additional skill table choice and skill roll step after the advancement step, giving the character one extra skill pick for that term.

## Found during

Manual testing (documented in TESTING.md).
