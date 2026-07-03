# Pre-Career Education (University / Military Academy)

Traveller lets a character attempt **Pre-Career Education** — University or a Military
Academy — after Childhood but before entering a career. The generator currently skips
this phase entirely: Childhood hands straight to Career Selection, so a player is only
ever offered careers and can never take the University/Academy path that grants extra
skills, characteristic boosts, and career-entry advantages.

## Problem

After the childhood term the engine goes directly to career selection. In
`src/terms/childhood.py:138`, `ChildhoodTerm.next_term()` builds a `TransitionTerm`
wrapping `ChooseCareerStep` with no opportunity to choose pre-career education first.
There is no term, step, or data representing University or Military Academy, so the
entire optional education phase (qualify → term of study → graduation check → optional
"honours"/commission benefit) is missing from character creation.

Per the rules, a character may attempt **one** pre-career education option (with age /
number-of-terms and characteristic eligibility limits), and it is optional — the player
must be able to decline and go straight to a career as today.

## Scope

- New domain code under `src/terms/` (likely a `src/terms/education/` package or module)
  for the education phase:
  - A choice step offered after Childhood: *Attempt University / Attempt Military Academy
    / Skip to career selection* (gated by eligibility, mirroring how
    `ChildhoodTerm.next_term` filters careers).
  - Qualification roll for the chosen institution (reuse `PassFailRollStep` in
    `src/terms/base.py`, as qualification/survival/advancement already do).
  - A study term granting skills / characteristic increases, and a graduation
    (and, for the Academy, commission/honours) resolution that can feed forward into
    the subsequent career (e.g. entry rank / DM, `pending_career_entry`-style handoff).
- Wire the new term(s) into the flow: `ChildhoodTerm.next_term()` (or a new intermediate
  term) routes into the education phase, whose `next_term(context)` ultimately produces
  the existing `TransitionTerm(ChooseCareerStep(...))`. The engine's
  `_advance_past_term_boundaries()` (`src/engine.py:55`) should chain through it with no
  API/frontend changes, per the self-describing-step contract.
- Carry any pre-career effects across the term boundary via `CareerContext`
  (`src/terms/context.py`) rather than session globals, consistent with the existing
  term-owned routing pattern.
- Represent institution data (qualification target, skill lists, graduation effects) as
  data files if it keeps parity with the YAML-driven career model, or inline if small —
  decide during design.
- Update `CLAUDE.md` and `AGENTS.md` architecture notes to describe the new phase.

## Done when

- [ ] After Childhood, the generator offers University, Military Academy, and a
      "skip to career" option (each gated by the relevant eligibility rules), and
      choosing skip reproduces today's behaviour.
- [ ] Attempting an institution runs a qualification roll; on success the character
      lives a study term that grants the appropriate skills/characteristic increases and
      resolves graduation (and Academy commission/honours) per the rules.
- [ ] The education phase feeds forward into the existing career flow — a graduate
      entering a career receives the rules-defined benefit (entry rank / DM / auto-entry)
      via `CareerContext`, with no changes required in `src/api.py` or the frontend.
- [ ] New tests cover: the post-childhood branch (education vs skip), qualification
      pass/fail, graduation success/failure, and the handoff into career selection —
      e.g. `uv run pytest tests/test_education.py` (new) and the existing
      `uv run pytest` suite stays green.

## Notes

- Ordering: this sits between `ChildhoodTerm` and the career flow; it reuses the
  `PassFailRollStep`, term-owned `next_term(context)`, and `CareerContext` patterns
  already in place, so no prerequisite item — but it is the natural next expansion of
  the lifepath beyond Childhood → Career.
- The pre-career/university → career linkage (auto-entry, DMs) should reuse the existing
  `pending_career_entry` / `force_auto_qualify` machinery in
  `src/terms/careers/terms.py` where it fits rather than inventing a parallel mechanism.
