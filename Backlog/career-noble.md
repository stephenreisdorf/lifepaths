# Add Noble career

Add `data/careers/noble.yaml` so Noble is selectable in career selection.

## Scope

- Qualification: SOC 10+ (automatic if SOC ≥ 10; otherwise unavailable). Current YAML loader / `RollQualificationStep` treats qualification as a 2d6 + DM roll — this career needs "automatically qualifies if characteristic ≥ target, otherwise ineligible" support.
- Assignments (each with its own Survival / Advancement):
  - Administrator — Survival INT 4+, Advancement EDU 6+
  - Diplomat — Survival INT 5+, Advancement SOC 7+
  - Dilettante — Survival SOC 5+, Advancement INT 8+
- Fill in service skills, per-assignment skill tables, events, mishaps, and rank table per the Noble career entry in the core rules.
