---
name: audit-perf
description: Audit the lifepaths codebase for performance issues and dead code (unreferenced functions/branches, redundant file/YAML re-reads or re-globbing, avoidable recomputation) and file each as a backlog candidate. One of the five focus audits behind `/audit ultimate`; also runnable standalone. Args: none (files to Backlog/) | "--candidates <output-file>" (coordinated mode).
---

# Audit — performance & dead code

Sweeps for wasted work and code that no longer earns its place. This is a small codebase, so the bar
is "concretely wasteful or genuinely unused," not micro-optimization.

**Output & argument handling:** follow `../audit/output-modes.md`. No arg → file to `Backlog/` (no
commit). `--candidates <output-file>` → append candidate blocks only. Read `Backlog/README.md` and
`Backlog/done/` first to avoid duplicates.

## Scope & sources

- **Under audit:** `src/` (all Python), `data/careers/*.yaml` access patterns, and hot paths in the
  term/step lifecycle.

## What to look for

- **Dead code:** functions, methods, branches, enum members, or module-level constants with no
  references. Verify with a repo-wide search (`grep`/Grep) before flagging — a symbol used only via a
  dispatch table or dynamic dispatch is *not* dead. Include the search you ran in the Problem.
- **Redundant I/O:** career YAML re-parsed/re-validated or the careers dir re-globbed more than once
  per session. Note the existing `CareerRepository` caching (`FilesystemCareerRepository`) and flag
  any path that still bypasses it.
- **Avoidable recomputation:** values recomputed every step that could be computed once; repeated
  serialization of unchanged state; O(n) scans where a dict keyed by name already exists.
- **Unreferenced test/fixture/data files or unused dependencies.**

## Recording a finding

Home category: **Architecture** (or a `## Performance` section if several land). Framing:
`## Opportunity`. For dead code, the Problem must show the reference search that came up empty (so the
reviewer can trust it's safe to delete). `## Done when` asserts the symbol is removed / the redundant
read is eliminated and `uv run pytest passes.` Keep severity honest — most perf/dead-code items here
are **low** unless they touch a real hot path or remove meaningful surface area.
