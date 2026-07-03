# Wire anagathics into the career term flow

The anagathics domain model landed (`src/terms/anagathics.py`, the
`AnagathicsCourse` state and mutators on `Character`, and the Ageing DM), but
nothing in the career flow ever invokes it. This wires the RAW start-of-term
mechanics into `CareerTerm`, completing the follow-up left by the
[anagathics](done/anagathics.md) item.

## Problem

`attempt_start_anagathics` and the course state exist but are dead code: a
Traveller can never actually start a course during creation. Per MgT 2022
(transcribed from the "Bowman Arm" NotebookLM notebook), three mechanics are
unimplemented:

- **Start-of-term choice** — "At the start of any career term, a Traveller can
  start taking anagathics by rolling SOC 10+."
- **Doubled Survival checks** — "The Traveller must make two Survival checks in
  each term instead of one. If either or both checks are failed, the Traveller
  suffers a Mishap."
- **Natural-2 → Prisoner** — "If you roll 2 exactly, you must instead go
  straight to the Prisoner career in this term."

The recurring cost ("1D×Cr25000 for each term the Traveller uses the drugs")
is charged on the starting term but never on continuing terms.

## Scope

- **Opt-in**: the optional anagathics rule is off by default so existing flows
  are unchanged. A `anagathics_enabled` flag on `CareerContext` (threaded from
  `GameSession` / `/api/start`) gates the offer; it is passed to every
  `CareerTerm` construction site.
- **New steps** (`src/terms/careers/steps.py`): `ChooseAnagathicsStep` (CHOICE,
  offered at term start when enabled and no active course) and
  `AnagathicsUpkeepStep` (AUTOMATIC, charges the per-term maintenance cost when
  a course is already active at term start).
- **`CareerTerm`**: prepend the anagathics step at term start (suppressed in the
  Prisoner career — "Travellers may not use Anagathics in prison"); extract
  `_build_initial_steps()`; add dispatch handlers; double the Survival check via
  a `_append_survival_check()` helper (fail either → Mishap); route a natural 2
  to Prisoner via `pending_career_entry` and a terminal `ANAGATHICS_PRISONER`
  status.
- **Dice** stay in `src/terms/anagathics.py` (a `maintain_anagathics` helper),
  not on the pure `Character`.

## Done when

- [ ] `uv run pytest` is green.
- [ ] With the rule enabled, a term start offers the anagathics choice; a SOC
      10+ result starts a course and charges 1D×Cr25000, and each continuing
      term charges again (may go into debt).
- [ ] While a course is active, two Survival checks are rolled and failing
      *either* triggers the Mishap branch.
- [ ] A natural 2 on the acquire roll routes the term straight to the Prisoner
      career.
- [ ] With the rule disabled (default), the career flow is byte-for-byte
      unchanged — existing tests pass without modification of their flow.
- [ ] New tests (`tests/test_anagathics_career.py`) cover the choice outcomes,
      the doubled Survival check, and the Prisoner routing.
- [ ] `CLAUDE.md` and `AGENTS.md` note the wiring.

## Notes

Follow-up to [anagathics](anagathics.md). Rules transcribed from the
"Bowman Arm" NotebookLM notebook (the repo's MgT 2022 source of truth).
Stopping a course (the immediate Ageing roll on discontinuation) has no trigger
yet and is out of scope here.

## Resolution

Wired the optional rule into the career flow:

- **Opt-in** via `CareerContext.anagathics_enabled` (off by default), threaded
  from `GameSession(anagathics_enabled=…)` and an optional `/api/start` body
  and passed to every `CareerTerm` construction site. Baseline flows are
  unchanged (existing 111 tests pass untouched).
- **Steps** (`src/terms/careers/steps.py`): `ChooseAnagathicsStep` (CHOICE) and
  `AnagathicsUpkeepStep` (AUTOMATIC), re-exported from the package.
- **`CareerTerm`**: `_anagathics_start_step()` opens a term on the offer (no
  course) or upkeep (active course), suppressed in the Prisoner career;
  `_build_initial_steps()` holds the real opening step so the anagathics handler
  can append it; `_append_survival_check()` + the reworked `_after_survival`
  double the check (fail either → Mishap); a natural 2 sets a terminal
  `ANAGATHICS_PRISONER` status routed to the Prisoner career via
  `pending_career_entry` / `_forced_entry_career_term`.
- **Dice** stay in `src/terms/anagathics.py` (`roll_anagathics_cost`,
  `maintain_anagathics`).
- Tests: `tests/test_anagathics_career.py` (12 tests). Verified end-to-end by
  driving a real `GameSession` (each career term ran two Survival checks, upkeep
  charged each continuing term, natural-2 routed to Prisoner).
