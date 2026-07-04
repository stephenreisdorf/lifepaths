---
name: audit-tests
description: Audit the lifepaths test suite for coverage gaps (untested StepStatus routes, effect types, aging/anagathics/muster-out edge cases, career-YAML validation) and file each gap as a backlog candidate naming the specific test that should exist. One of the five focus audits behind `/audit ultimate`; also runnable standalone. Args: none (files to Backlog/) | "--candidates <output-file>" (coordinated mode).
---

# Audit — test coverage gaps

Maps `tests/` against `src/` to find behavior that isn't exercised, then files each gap as an
actionable "add this test" item.

**Output & argument handling:** follow `../audit/output-modes.md`. No arg → file to `Backlog/` (no
commit). `--candidates <output-file>` → append candidate blocks only. Read `Backlog/README.md` and
`Backlog/done/` first to avoid duplicates.

## Scope & sources

- **Under audit:** the whole `tests/` tree against `src/`.
- **Baseline:** run `uv run pytest` first and confirm it's green. A red baseline is itself the top
  finding — report it and stop filing coverage items until it's green.

## What to look for

Prioritize branches whose failure would be silent or costly:

- **Terminal routing:** each `StepStatus` route out of `CareerTerm` / `TransitionTerm`
  (`FAILED_QUAL`, `MISHAP`, `EVENT`, `FORCED_EXIT`, `FORCED_STAY`, `COMPLETED`,
  `ANAGATHICS_PRISONER`) — is every branch of `next_term` / the dispatch handlers covered?
- **Effects:** every typed effect in `src/terms/effects.py` (`skill`, `characteristic`, `associate`,
  `forced_exit`, `enter_career`, `life_event`, `injury`, `betrayal`, flavor-only DMs) and the
  recursive life-event/injury `{rolls, take}` paths.
- **Edge cases:** characteristic reductions flooring at 0; skill-level budget cap enforcement; aging
  worst-row INT hit; anagathics start/maintain/stop and doubled survival check; muster-out benefit
  rolls; draft-once-per-life / drifter fallback.
- **Data validation:** does every `data/careers/*.yaml` load and validate (`extra="forbid"`) under a
  test? Rank tables, qualification shapes, skill-table shapes.
- **Determinism:** tests that should seed `rng` but don't (flaky-by-dice risk).

## Recording a finding

Home category: **Architecture** (test infrastructure) — or **Bugs** if the gap plausibly hides a live
defect (say why). Framing: `## Opportunity`. Each `## Done when` must name the concrete test that
should exist and pass, e.g. `- [ ] uv run pytest tests/test_effects.py::test_injury_take_lower passes.`
Cite the `src/...:line` branch that's currently uncovered.
