# Gate Advanced Education skill table on EDU 8+

Per the rules, the Advanced Education skill table typically requires EDU 8+. `ChooseCareerSkillsTable` (`src/terms/careers.py:108-136`) exposes every table listed in the YAML unconditionally.

## Fix

- Extend the YAML skill-table schema to support per-table requirements (e.g. `requires: { characteristic: EDU, min: 8 }`).
- Filter options in `ChooseCareerSkillsTable.prompt()` based on the character's current characteristics.
- Consider whether to hide the table entirely or show it as disabled with a reason.
