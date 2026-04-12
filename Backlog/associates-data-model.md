# Add Contacts / Allies / Rivals / Enemies data model

Per the rules, Travellers accumulate four kinds of associates: Contact, Ally, Rival, Enemy. `Character` (`src/character.py:46-99`) has no field for these.

## Scope

- Add `Associate` model: `name`, `type` (enum: contact/ally/rival/enemy), `description`, `source_event` (optional).
- Add `associates: list[Associate]` (or dict) on `Character`.
- Serialize in `GameSession._character_summary` (`src/engine.py:30-46`).
- Prerequisite for event/mishap effects that grant associates.
