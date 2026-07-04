---
name: audit-rules
description: Audit the lifepaths codebase for rules fidelity against Mongoose Traveller 2022 (the "Bowman Arm" NotebookLM notebook, the repo's rules source of truth) and file each divergence as a backlog candidate with RAW-vs-code numbers. One of the five focus audits behind `/audit ultimate`; also runnable standalone. Args: none (files to Backlog/) | "--candidates <output-file>" (coordinated mode).
---

# Audit — rules fidelity vs Mongoose Traveller 2022

Sweeps the implemented rules for divergences from **Mongoose Traveller 2022 Core Rulebook**, the
repo's declared source of truth. The rulebook is not in the repo (copyright); it lives in the
**"Bowman Arm" NotebookLM notebook** — query it via the `notebooklm` skill to transcribe exact
tables/mechanics, exactly as `CLAUDE.md` prescribes for fidelity work.

**Output & argument handling:** follow `../audit/output-modes.md`. No arg → file findings to
`Backlog/` (no commit). `--candidates <output-file>` → append candidate blocks to that file only.
Read `Backlog/README.md` and skim `Backlog/done/` first so you don't re-file known or shipped items
(several fidelity items have already shipped, e.g. `done/pre-career-education-rules-fidelity.md`).

## Scope & sources

- **Code under audit:** `data/careers/*.yaml`, `src/terms/` (childhood, education, careers, effects,
  life_events, anagathics, aging), `src/career_data.py`, `src/character.py`, `src/utilities.py`.
- **Reference:** the "Bowman Arm" NotebookLM notebook via `/notebooklm` — query it for the exact
  table/number before flagging a divergence. Never assert a RAW value from memory; transcribe it.

## What to look for

Compare code against RAW for at least:

- **Characteristic DM** — `value // 3 - 2` (`src/character.py`) vs the RAW DM table.
- **Aging** — the `AGING_TABLE` and DM in `src/terms/careers/aging.py` (2D − terms served, worst-row
  INT hit).
- **Qualification / survival / advancement** targets and DMs per career YAML.
- **Rank bonuses** — `apply_rank_bonus` and each career's `ranks:` table (bonus skills / characteristic
  bumps, the rank-0 entry skill, the documented choice-case fallbacks).
- **Skill tables & service skills** — per-assignment tables, background/service skill counts, the
  skill-level budget cap (`total_skill_level_cap`).
- **Muster-out** — cash and benefits tables (`src/terms/careers/muster_out.py` + YAML).
- **Events / mishaps / life events / injury** — `src/terms/effects.py`, `src/terms/life_events.py`
  (2D life-events table, 1D injury table, "roll twice take lower/higher").
- **Anagathics** — the SOC 10+ entry roll, cost (1D×Cr25000), aging DM (`src/terms/anagathics.py`).
- **Pre-career education** — university/academy eligibility, qualification, graduation bumps
  (`src/terms/education/config.py`).

## Recording a finding

Home category: **Bugs** (or a `## Fidelity` section if several land). Framing: `## Scope`. For each
divergence, quote the **RAW number in bold** vs the **code number in bold** in the Problem and Notes
(the established fidelity-item style), cite the exact `path:line` and the career YAML, and cite the
NotebookLM query result you relied on. `## Done when` should assert the code matches RAW and
`uv run pytest passes.`
