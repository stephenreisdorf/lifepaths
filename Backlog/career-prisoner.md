# Add Prisoner career

Add `data/careers/prisoner.yaml` so Prisoner is available as a special career.

## Scope

- Qualification: special — Prisoner cannot be chosen during normal career selection. Characters only enter it via specific events/mishaps in other careers. `ChooseCareerStep` must exclude Prisoner from its options, and the engine needs a way to force entry into Prisoner from an event/mishap outcome (ties into `Backlog/events-effects.md` and `Backlog/mishap-effects.md`).
- Assignments (each with its own Survival / Advancement):
  - Inmate — Survival END 7+, Advancement STR 7+
  - Thug — Survival STR 8+, Advancement END 6+
  - Fixer — Survival INT 9+, Advancement END 5+
- Fill in service skills, per-assignment skill tables, events, mishaps, and rank table per the Prisoner career entry in the core rules.
