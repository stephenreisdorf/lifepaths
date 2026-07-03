# First term of a *subsequent* career skips its skill-table roll

Basic training replacing the skills-and-training roll should apply only to the
character's **very first career ever**. For the first term of any *later* career,
the character gains one Service Skill at level 0 **and** still rolls once on a
chosen skill table. The implementation skips that roll on every first term,
under-granting skills to multi-career characters.

## Problem

In `CareerTerm`, `_after_qualification` (`src/terms/careers/terms.py`) routes the
first term to Basic Training / PickServiceSkill → ChooseAssignment, and
`_after_assignment` for a first term appends only the `SurvivalCheckStep` — no
`ChooseCareerSkillsTable` / `RollForSkillStep`. So *every* first term omits the
skill-table roll.

Per Core Rulebook.pdf (Mongoose Traveller 2022, Skills and Training / Basic
Training): the "all Service Skills at level 0 instead of a skill roll" substitution
is for the **first career only**. Subsequent careers get one skill at level 0
from basic training **plus** the normal per-term skill roll starting in term 1.

The code already distinguishes the two cases for basic training itself
(`BasicTrainingStep` when `not self.character.careers` vs `PickServiceSkillStep`
otherwise) — the missing piece is appending a skill-table roll on the first term
when this is *not* the first career.

Identified by a NotebookLM audit against Core Rulebook.pdf.

## Scope

- `src/terms/careers/terms.py` — on a first term where the character already has
  at least one prior career, insert the `ChooseCareerSkillsTable` →
  `RollForSkillStep` sequence (as subsequent terms do) before/around the survival
  check, matching the RAW ordering. Leave the genuine first-career-ever path
  (all Service Skills at level 0, no roll) unchanged. Mind the Citizen/Drifter
  `basic_training_from_assignment` variant so it isn't double-granted.

## Done when

- [ ] A character entering their **second** career rolls once on a skill table
      during that career's first term (in addition to the one level-0 service
      skill from basic training).
- [ ] A character's **first** career's first term is unchanged: all Service Skills
      at level 0 and no skill-table roll.
- [ ] A test in `tests/test_career_transitions.py` covers both cases.
- [ ] `uv run pytest` is green.

## Notes

Confirm the exact wording/ordering against the rulebook in use before landing —
this one hinges on a flowchart/step reading and is the most edition-sensitive of
the fidelity items. Independent of the education/aging/muster items.
</content>
