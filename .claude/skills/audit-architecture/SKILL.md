---
name: audit-architecture
description: Audit the lifepaths backend for architecture, layering, and coupling problems (Domain→Engine→API violations, god classes, spots that break the codebase's own dispatch-table/PassFailRollStep/repository conventions, dict-vs-typed boundaries) and file each as a backlog candidate. One of the five focus audits behind `/audit ultimate`; also runnable standalone. Args: none (files to Backlog/) | "--candidates <output-file>" (coordinated mode).
---

# Audit — architecture & coupling

Sweeps the Python backend for structural problems: layering violations, tight coupling, god classes,
and — importantly for this repo — places that break the codebase's *own* established conventions.

**Output & argument handling:** follow `../audit/output-modes.md`. No arg → file to `Backlog/` (no
commit). `--candidates <output-file>` → append candidate blocks only. Read `Backlog/README.md`'s
`## Architecture` section and `Backlog/done/` first — several architecture refactors are already
open or shipped; don't duplicate them.

## Scope & sources

- **Code under audit:** `src/engine.py`, `src/api.py`, `src/terms/` (base, context, careers,
  education, effects), `src/career_data.py`, `src/career_loader.py`, `src/career_repository.py`,
  `src/character.py`.
- **Reference:** `CLAUDE.md`'s Architecture + Key patterns sections are the intended design; measure
  drift against them. The `python-clean-architecture` skill's principles are a useful cross-check.

## What to look for

- **Layering:** Domain (`src/terms/`, `src/character.py`) must not import Engine or API; the API
  (`src/api.py`) must stay generic (no knowledge of specific step types). Flag upward imports or
  leaks.
- **Convention drift** — the repo has strong patterns; flag code that *doesn't* follow them:
  - if/elif chains where a declarative dispatch table is the house style (`_STEP_HANDLERS`,
    `_NEXT_TERM_HANDLERS`, `_TERMINAL_HANDLERS`).
  - duplicated pass/fail roll boilerplate instead of subclassing `PassFailRollStep`.
  - filesystem/loader access that bypasses the injected `CareerRepository` on `CareerContext`.
  - duplicated `resolve()` validation across choice steps (single-choice base opportunity).
- **Coupling & god classes:** does one class reach into many domain models' internals (e.g. engine
  serialization touching every model)? Split candidates.
- **Typed-vs-dict boundaries:** dicts passed where a validated Pydantic model exists, or models
  converted to dicts too early/late relative to the generic `StepPrompt`/`StepOutcome` API contract.
- **Duplication:** repeated context-reset blocks, repeated parsing, copy-pasted term wiring.

## Recording a finding

Home category: **Architecture**. Framing: `## Opportunity`. Name the convention being violated and
the in-repo exemplar to mirror. In `## Notes`, state it's a **no-behavior-change** refactor and flag
`CLAUDE.md` / `AGENTS.md` upkeep if the change alters an architectural note. `## Done when` asserts the
structural condition (e.g. "routing goes through a status→handler table") and `uv run pytest passes.`
