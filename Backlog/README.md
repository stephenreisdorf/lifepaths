# Backlog

One file per open issue. Index below.

## Bugs

_(none)_

## UX

_(none)_

## Architecture

- [Pull advance() dispatch into a DispatchTerm base](dispatch-term-base.md) — identical dispatch body copy-pasted across four terms.
- [Extract the best-of-options qualification helper](dedup-best-qualification-option.md) — duplicated max()-by-DM block in CareerTerm and AssignmentChangeTerm.
- [Keep CareerData typed through the domain layer](typed-career-data-through-domain.md) — validated model flattened to loose dicts at the domain boundary.
- [Hoist in-function career_loader imports](hoist-career-loader-imports.md) — seven deferred imports with no cycle to justify them.

## Deferred

- [Connections Rule (multi-character)](connections-rule.md) — shared events between two Travellers; requires multi-character session model. May be deferred indefinitely for single-player use.
- [Anagathics](anagathics.md) — anti-aging drugs (SOC 10+, cost/risk) not modelled; sequence after the official aging table.
