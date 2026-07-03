# Aging uses a homebrew system instead of the official Ageing table

The aging mechanic is a custom per-characteristic, per-bracket target system that
bears no relation to the official Traveller Ageing rules. This is the single
largest rules divergence found in the audit.

## Problem

`src/terms/careers/aging.py` implements `AGING_TABLE` as age brackets (34–49,
50–65, 66–73, 74+), each rolling a **separate 2D check per physical
characteristic** (e.g. STR 8+, DEX 7+, END 8+) and applying a fixed penalty on
failure.

The Core Rulebook.pdf (Mongoose Traveller 2022, Ageing) instead uses a **single
2D roll on one Ageing table**, with **DM = −(total number of terms served)**, and
graded results ranging from "No effect" down to "Reduce three physical
characteristics by 2" (worse outcomes at lower totals). The current
implementation captures none of this: no single unified roll, no
terms-served DM, no graded result row.

Aging also currently triggers at age ≥ 34 evaluated end-of-term; verify the
official trigger cadence (per term after the fourth term / age 34) matches once
the table is replaced.

Identified by a NotebookLM audit of the implemented rules against Core
Rulebook.pdf.

## Scope

- `src/terms/careers/aging.py` — replace `AGING_TABLE` and `AgingStep` internals
  with the official single-2D-roll-with-terms-DM Ageing table and its graded
  result rows. Preserve the existing step contract (`AgingStep` id/type, the
  `StepOutcome` shape, and the `AGING_CRISIS` death flag when a characteristic
  hits 0) so `CareerTerm._finalize_term` / `_after_aging` need no changes.
- Keep the terms-served count available to the step (it drives the DM).

## Done when

- [ ] `AgingStep` makes a single 2D roll with a DM equal to −(terms served) and
      resolves it against the official graded Ageing result rows.
- [ ] The per-bracket `AGING_TABLE` structure is gone (or repurposed to encode the
      official result rows), with no per-characteristic target checks.
- [ ] A test pins representative outcomes (e.g. a high roll → no effect; a low
      effective total → the documented multi-characteristic reduction) using
      seeded dice via `src.utilities.rng`.
- [ ] The `AGING_CRISIS` / death-at-0 behaviour still fires.
- [ ] `uv run pytest` is green.

## Notes

Larger than the other fidelity items — it is a wholesale mechanic replacement.
Transcribe the exact result table from the rulebook in use. Independent of the
education and muster-out items.
</content>
