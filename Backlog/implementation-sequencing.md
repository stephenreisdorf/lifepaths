# Backlog Implementation Sequencing

## Context
Backlog/ has ~30 open issues. This document sequences them into waves where each wave's items can be worked on in parallel (multiple agents / contributors / branches) without file-level conflicts, and where later waves safely build on earlier foundations.

Concurrency is constrained by two hot files that nearly every mechanic touches:
- `src/terms/careers.py`
- `src/character.py`

Per-career YAML under `data/careers/` is the cheapest axis of parallelism — one file per career, no shared edits.

## Legend
- **[CODE: path]** — primary file(s) modified
- **deps:** items that must land first

---

## Wave 1 — Foundations (fully parallel, ~7 concurrent streams)

These items have no backlog dependencies and touch mostly-disjoint files. Run them all concurrently.

1. **skill-notation-parsing** [CODE: `src/terms/careers.py` — `RollForSkillStep` only]
   Gatekeeper for all later skill work. Handle level 0 / bare / explicit level.
2. **terms-served-on-mishap** [CODE: `src/terms/careers.py` — `MishapRollStep` / `CareerTerm` only]
   One-line-ish fix: increment `terms_served` on mishap-ended terms.
3. **track-career-ejection** [CODE: `src/character.py` — `CareerRecord.ejected` flag]
   Prerequisite for assignment-change-flow.
4. **associates-data-model** [CODE: `src/character.py` — new `Associate` model + `Character.associates`]
   Prerequisite for connections-rule and events/mishaps that grant contacts.
5. **no-reentry-next-term** [CODE: `src/engine.py`, `src/career_loader.py` — `GameSession.blocked_career` + filter]
   Orthogonal to everything else.
6. **advanced-education-edu-gate** [CODE: `src/career_loader.py` YAML schema + `ChooseCareerSkillsTable`]
   Existing gated-table machinery already handles this shape; just wire the EDU gate.
7. **Career YAMLs — "easy" batch** [CODE: new `data/careers/{agent,merchant,rogue,scholar,scout}.yaml`]
   Five careers that need no new mechanics. One file each → trivially parallel.

**Serialization note within Wave 1:** items (1), (2) both edit `careers.py` but in separate classes — low-risk merge. Items (3), (4) both edit `character.py` but add disjoint fields — low-risk merge. If a single contributor is doing both of a pair, bundle them into one commit.

---

## Wave 2 — Build on foundations (4 concurrent streams)

Kicked off once Wave 1 is merged.

1. **skill-level-cap-4** + **total-skill-levels-cap** [CODE: `src/character.py` — `increment_skill`]
   Bundle: both modify the same method. One stream.
   deps: skill-notation-parsing.
2. **basic-training-subsequent-careers** [CODE: `src/character.py` flag, `src/terms/careers.py` — `CareerTerm`/`BasicTrainingStep`]
   deps: none new.
3. **advancement-roll-forces-exit** [CODE: `src/terms/careers.py` — `AdvancementRollStep.apply`, `CareerTerm.next_term`]
   deps: none; but will conflict in `careers.py` with (2). Sequence (3) after (2) or have the same contributor own both.
4. **assignment-change-flow** [CODE: `src/terms/careers.py` — `ContinueOrMusterOutStep` branch]
   deps: track-career-ejection (Wave 1).
5. **Career YAMLs — Drifter** [CODE: `data/careers/drifter.yaml`]
   deps: none strictly, but unlocks Wave 3's draft-and-drifter-fallback.

**Key constraint:** (2), (3), (4) all edit `careers.py`. Either assign all three to the same owner, or stage them as serialized commits on one branch. Everything else in Wave 2 is genuinely parallel.

---

## Wave 3 — Effects + officer track (3 concurrent streams)

1. **events-effects + mishap-effects** [CODE: new `src/terms/effects.py`, `src/character.py` effect methods, YAML schema extensions in every career file]
   Bundle together — they share the effect-applier. Single stream.
   Creates the effect vocabulary (skill grant, characteristic bump, contact, forced exit, injury) that muster-out and prisoner-entry reuse.
   deps: associates-data-model (Wave 1) for contact effects.
2. **commission-step + officer-track** [CODE: `src/terms/careers.py`, `src/career_loader.py`, `src/character.py` `CareerRecord.commissioned`]
   Bundle: officer-track is meaningless without commission. Single stream.
   deps: advancement-roll-forces-exit (Wave 2).
3. **Career YAMLs — Army, Marine, Citizen, Entertainer, Noble** [CODE: per-file YAMLs + small `career_loader.py` extensions for OR-logic + auto-qual]
   - Army/Marine ride on the officer-track work landing in (2); start them after (2) lands *or* stub commission flag for now.
   - Entertainer needs OR-qualification support in `career_loader.py` — small.
   - Noble needs auto-qualification support — small.
   - Citizen needs citizens-drifters-basic-training (schedule after Wave 4 or stub).

---

## Wave 4 — Reuse the effect machinery (parallel streams)

1. **muster-out-benefits** [CODE: new `MusterOutStep` in `careers.py`, benefits loader in `career_loader.py`, effect-applier reuse]
   deps: events-effects+mishap-effects (Wave 3) for the effect-applier pattern; officer-track (Wave 3) for rank-bonus tables.
2. **draft-and-drifter-fallback** [CODE: `src/engine.py`, new `ChooseDraftOrDrifterStep` in `careers.py`, new `data/careers/draft.yaml` table]
   deps: drifter YAML (Wave 2), no-reentry-next-term (Wave 1).
3. **citizens-drifters-basic-training** [CODE: `src/terms/careers.py` step reordering]
   deps: basic-training-subsequent-careers (Wave 2).
4. **Career YAML — Prisoner** [CODE: `data/careers/prisoner.yaml` + exclusion logic]
   deps: events-effects / mishap-effects (Wave 3) — prisoner entry is an effect.

---

## Wave 5 — Long tail (lower priority, parallel)

1. **aging** [CODE: `src/character.py` age field, new `AgingStep` in `careers.py`]
   Independent — could actually run as early as Wave 2. Parked here because it's not blocking anything and confirms rules scope.
2. **connections-rule** [CODE: `src/engine.py` multi-character architecture]
   Large, deferred per the issue itself. Blocked by associates-data-model only, but scope warrants its own planning pass.

---

## Critical-path summary

```
Wave 1 (parallel)  →  Wave 2 (parallel)  →  Wave 3 (parallel)  →  Wave 4 (parallel)
  foundations         skill caps +            effects +              muster-out +
  7 streams           advancement +           officer track +        draft fallback +
                      assignment change       stub-needy careers     remaining careers
                      5 streams               3 streams              4 streams
```

If one contributor owns `src/terms/careers.py` per wave (to avoid merge friction) and others fan out on YAMLs and `character.py`, every wave should land quickly.

## Files critical to nearly every wave
- `src/terms/careers.py` — treat as a serialization point; one owner per wave.
- `src/character.py` — multiple streams can extend it if they add disjoint fields/methods.
- `src/career_loader.py` — schema extensions should land together at the start of each wave.
- `data/careers/*.yaml` — per-file, naturally parallel.

## Verification per wave
- Run `uv run python main.py` and the Vue frontend end-to-end through character creation for each newly-supported path.
- After each career YAML lands, spot-check it loads via `uv run python -c "from src.career_loader import load_career; load_career('<name>')"`.
