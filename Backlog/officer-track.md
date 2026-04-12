# Officer skill table and Officer rank track

Tied to the Commission step. `AdvancementRollStep` (`src/terms/careers.py:278-359`) uses a single `ranks` list with no officer/enlisted distinction, and there is no separate Officer skill table available to commissioned characters.

## Scope

- YAML loader: support separate `officer_ranks` and `officer_skill_table` entries for military careers.
- `AdvancementRollStep` and rank-bonus lookup: pick enlisted vs. officer track based on `CareerRecord.commissioned`.
- `ChooseCareerSkillsTable`: include Officer skill table in options only if commissioned.
- Depends on commission-step backlog item.
