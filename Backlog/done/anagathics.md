# Anagathics are not modelled

The Core Rulebook's optional anagathic (anti-aging) drugs rule is not implemented:
no way to start a course, no SOC 10+ requirement, and no cost/availability/risk
handling. Low priority for a baseline creator, captured so the omission is tracked.

## Problem

There is no anagathics concept anywhere in the domain layer. Per Core Rulebook.pdf
(Mongoose Traveller 2022), a character of SOC 10+ may take anagathics to offset
aging effects, at a recurring cost and with availability/failure risk. None of
this exists in `src/character.py`, the aging step, or muster-out/cash handling.

Identified by a NotebookLM audit against Core Rulebook.pdf.

## Scope

- Model an anagathics course on the character (active/inactive, ongoing cost).
- Gate starting a course on SOC ≥ 10.
- Interact with aging: offset or negate aging effects while the course is
  maintained, per RAW.
- Handle cost/availability against `character.cash`.

## Done when

- [ ] A character can begin an anagathics course only at SOC ≥ 10.
- [ ] Maintaining the course modifies aging outcomes per the rulebook.
- [ ] The recurring cost is deducted appropriately.
- [ ] Tests cover the SOC gate and the aging interaction.

## Notes

Best sequenced **after** the official [Ageing table](aging-official-table.md) lands,
since anagathics modify that system — building it against the current homebrew
aging would be throwaway work. Niche/optional; deferred until the core aging
fidelity work is done.

## Resolution

Implemented at the domain layer against the transcribed MgT 2022 rule (queried
from the "Bowman Arm" NotebookLM notebook):

- `AnagathicsCourse` on `Character` (`terms_used`, `total_cost`, `active`) plus
  `start_anagathics_course` / `maintain_anagathics_course` /
  `stop_anagathics_course` / `anagathics_aging_dm`.
- `src/terms/anagathics.py::attempt_start_anagathics` — the RAW **SOC 10+**
  entry roll (2D + SOC DM; natural 2 → Prisoner) and the **1D×Cr25000/term**
  cost deducted from `cash` (may go into debt). Done-when item 1's "SOC ≥ 10"
  is the source's actual "rolling SOC 10+" characteristic check.
- `AgingStep` adds `anagathics_aging_dm()` as a positive DM (offsetting
  −(terms served)) and reports it in the outcome description/data.
- Tests: `tests/test_anagathics.py` (9 tests) cover the SOC gate, the natural-2
  Prisoner outcome, the recurring cost/debt, and the Ageing interaction.

**Left as follow-up (beyond this item's domain-model scope):** wiring an
interactive start-of-term choice into `CareerTerm`, the RAW doubled Survival
checks while on a course, and routing a natural 2 into a Prisoner career.

