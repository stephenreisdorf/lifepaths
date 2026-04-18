# Backlog

One file per open issue. Index below.

## Bugs

- [Option to muster out on failed survival](muster-out-on-failed-survival.md) — failed survival forces new career selection with no muster-out choice.

## UX

- [Automatic steps should show feedback](automatic-step-feedback.md) — auto-resolved steps skip past silently; user should confirm and see results.

## Architecture

- [Career step sequencing machine](career-step-sequencing-machine.md) — extract `CareerTerm.advance()` from a 160-line if-elif into a testable, declarative form.
- [Split careers.py mega-module](split-careers-module.md) — break the 2042-line file into focused sub-modules (steps, terms, muster-out, aging, parsers).
- [Consolidate skill grant API](consolidate-skill-grant-api.md) — unify three overlapping skill-mutation methods and the parallel effects implementation.
- [Typed career data model](typed-career-data-model.md) — replace raw-dict splatting with a validated Pydantic model between YAML loader and CareerTerm.
- [Engine session state](engine-session-state.md) — replace mutable session flags with a typed career context object passed explicitly to terms.

## Deferred

- [Connections Rule (multi-character)](connections-rule.md) — shared events between two Travellers; requires multi-character session model. May be deferred indefinitely for single-player use.
