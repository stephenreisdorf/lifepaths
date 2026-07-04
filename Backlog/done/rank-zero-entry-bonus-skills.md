# Rank-0 entry bonus skills are never granted (Army / Marine / Prisoner)

In MgT 2022 exactly three careers grant a bonus skill the moment you enter at
Rank 0 — Army (Gun Combat 1), Marine (Gun Combat (any) 1 **or** Melee (blade) 1),
and Prisoner (Melee (unarmed) 1). The engine never applies a rank-0 bonus, and
all three YAML rank tables are mis-transcribed, so these entry skills are lost
and several other rank bonuses land on the wrong rank.

## Problem

Two independent defects, both verified against the "Bowman Arm" NotebookLM
transcription of the rulebook rank tables:

1. **Engine gap.** Career entry (`src/terms/careers/terms.py:396` `_after_qualification`)
   creates the `CareerRecord` at the default rank 0 (`src/character.py:50`) but
   never applies a starting-rank bonus. `_apply_rank_bonus` / the rank-bonus
   parser (`src/terms/careers/steps.py:598-614`) run **only on promotion**
   (`AdvancementRollStep`) and commission. So even a correctly-authored rank-0
   `bonus_skill` would be silently ignored.

2. **Data errors** in the three careers that actually have a rank-0 skill.
   Every other career's rank table checked (Navy, Merchant, Scout, …) matches
   the rulebook exactly — Navy is a perfect row-for-row match — so this is
   isolated to these three, not a global offset:

   - **`data/careers/army.yaml`** — whole enlisted table shifted up one rank.
     Rulebook: Gun Combat 1 @0, Recon 1 @1, Leadership 1 @3.
     YAML: Gun Combat @1, Recon @2, Leadership @4 (rank 0 blank).
   - **`data/careers/marine.yaml`** — rank-0 "Gun Combat (any) 1 **or** Melee
     (blade) 1" choice dropped entirely; rank 3 (Lance Sergeant) is `Gun Combat`
     but the rulebook grants **Leadership 1** there. (rank 1 Gun Combat and
     rank 5 END+1 are correct.)
   - **`data/careers/prisoner.yaml`** — rulebook is Melee (unarmed) 1 @0,
     Athletics 1 @1, Advocate 1 @2, END +1 @4. YAML is blank @0,
     Melee (unarmed) @1, Streetwise @2, Leadership @4 — rank-0 skill missing and
     ranks 1/2/4 bonuses all wrong.

3. **Schema limitation.** Marine's rank-0 is a *player choice* between two
   skills. `Rank.bonus_skill: str | None` (`src/career_data.py:99-107`) and the
   `_apply_rank_bonus` string parser can only express a single fixed grant, so
   representing the choice needs either a small schema extension or a documented
   convention (e.g. resolve to a `CHOICE` step at entry).

## Scope

- Domain/engine: grant the rank-0 `bonus_skill` on career entry. `_apply_rank_bonus`
  already resolves both "<Char> +N" bumps and plain skills, so entry can reuse it
  — the missing piece is a call at the point the record is first created at rank 0
  (`_after_qualification`, and the mid-career assignment-change reset at
  `terms.py:762-764`, which per RAW also resets to rank 0). Confirm it fires once
  per career entry, not on every term.
- Data: re-transcribe the rank-0 (and mis-shifted) rows in `army.yaml`,
  `marine.yaml`, `prisoner.yaml` against the rulebook.
- Schema: decide how to encode Marine's two-skill rank-0 choice (extend
  `Rank`/`bonus_skill`, or a documented single-skill fallback) and note it in
  `career_data.py` + `CLAUDE.md`/`AGENTS.md`.
- Verify the officer rank tables too — Army officer ranks 4/5/6 looked off in a
  first pass (YAML: Leadership@4, SOC+1@5, none@6; rulebook appeared to place a
  SOC benefit at General) but NotebookLM's officer-table read was lower
  confidence, so re-query before changing.

## Done when

- [ ] Entering Army as a first career grants Gun Combat at rank 0 (before any
      advancement roll); entering Prisoner grants Melee (unarmed) at rank 0;
      entering Marine grants the rank-0 skill (per the chosen encoding).
- [ ] `army.yaml`, `marine.yaml`, `prisoner.yaml` rank tables match the rulebook
      row-for-row (rank-0 skills present; Army un-shifted; Marine rank 3 =
      Leadership; Prisoner ranks 1/2/4 = Athletics/Advocate/END+1).
- [ ] A test asserts the rank-0 grant on entry for at least Army and Prisoner
      (e.g. `uv run pytest tests/test_career_transitions.py`), and the existing
      suite stays green.
- [ ] Marine's rank-0 choice encoding is documented in `career_data.py` and the
      agent guidance files.

## Notes

- Source of truth is the "Bowman Arm" NotebookLM notebook (see
  [rulebook-notebooklm-source]). Rank-0 facts here carry direct rulebook
  citations; the Prisoner ranks 1/2 and all officer-table rows were lower
  confidence in the transcription — re-verify those specific rows before editing.
- Independent of the deferred [Connections Rule](connections-rule.md); this is a
  Bugs-category fidelity fix, not a new feature.
- Touches the same rank-bonus code as [Keep Rank typed through steps](typed-rank-through-steps.md).
  That refactor factors one `apply_rank_bonus` helper — a natural place to add the
  entry-time call, so the two are worth sequencing together (the typed refactor
  first, then reuse its helper here).
