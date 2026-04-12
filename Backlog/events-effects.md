# Apply mechanical effects for events

`EventsRollStep.apply()` (`src/terms/careers.py:262-264`) is flavor-only. Events should grant skills, contacts/allies/rivals/enemies, benefits, and advancement/commission DMs.

## Scope

- Extend the YAML events schema to describe structured effects.
- Effect applier should handle: skill grants (specific or player choice), associate creation, bonus DMs to subsequent rolls in the same term, Life Events table redirection.
- Some events branch (skill check → consequence); may need additional step types.
- Life Events table is a separate referenced resource (see `[[09 - Life Events]]`); stub it out or implement as a sub-step.
