# Add Entertainer career

Add `data/careers/entertainer.yaml` so Entertainer is selectable in career selection.

## Scope

- Qualification: DEX 5+ OR INT 5+ (either characteristic may be used). Current YAML loader / `RollQualificationStep` only supports a single characteristic — the loader will need to support an either-of qualification, or this career needs a new qualification mode.
- Assignments (each with its own Survival / Advancement):
  - Artist — Survival SOC 6+, Advancement INT 6+
  - Journalist — Survival EDU 7+, Advancement INT 5+
  - Performer — Survival INT 5+, Advancement DEX 7+
- Fill in service skills, per-assignment skill tables, events, mishaps, and rank table per the Entertainer career entry in the core rules.
