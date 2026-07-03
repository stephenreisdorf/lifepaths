# Backlog

One file per open issue. Index below.

## Bugs

- [Characteristic DM wrong for a score of 0](characteristic-dm-zero.md) — `value // 3 - 2` yields −2 at 0; RAW is −3.
- [Pre-career education rules fidelity](pre-career-education-rules-fidelity.md) — University/Academy targets, bonus stats, and graduation checks diverge from RAW.
- [Aging uses a homebrew system](aging-official-table.md) — per-characteristic bracket checks instead of the official single-2D Ageing table with terms-served DM.
- [Muster-out omits the Rank 5–6 benefit DM](muster-out-rank-benefit-dm.md) — senior veterans miss the +1 DM to all Benefit rolls.
- [Subsequent-career first term skips its skill roll](subsequent-career-first-term-skill-roll.md) — the skill-roll substitution should apply to the first career only.
- [Life Events and Injury tables are flavor-only](life-events-injury-tables.md) — "roll on the Life Events / Injury table" entries carry no mechanics.

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
