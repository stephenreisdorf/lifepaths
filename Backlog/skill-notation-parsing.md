# Honor skill table notation (level 0 / no level / explicit level)

Per the rules, skill table entries have three forms:

| Entry | Meaning |
|-------|---------|
| `Gambler 0` | Gain Gambler at level 0 (only useful if no Gambler yet) |
| `Vacc Suit` (no level) | Gain Vacc Suit at level 1, or +1 if already have it |
| `Streetwise 1` | Gain Streetwise at level 1; if already level 1+, no benefit |

`RollForSkillStep` (`src/terms/careers.py:147-153`) just calls `increment_skill(self.skill, specialty="TODO")` for every entry regardless of notation. Related to the existing BACKLOG item `skill-table-plus-n-parsing.md`.

## Fix

- Parse skill entries into `(name, level_or_none, is_increment)` tuples.
- Apply semantics:
  - `"<name> 0"` → `add_skill(name)` (no-op if present).
  - `"<name>"` bare → if present, +1; else add at level 1.
  - `"<name> N"` → if current level < N, raise to N; else no-op.
- Replace `specialty="TODO"` with proper specialty handling (skill parents like Gun Combat, Pilot, Science have named specialties).
