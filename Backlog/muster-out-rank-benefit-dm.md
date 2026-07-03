# Muster-out omits the Rank 5–6 benefit-roll DM

A character who reaches Rank 5 or 6 in a career should get **DM +1 on every
muster-out Benefit roll** from that career, on top of extra rolls. The
implementation grants the extra rolls but never applies the DM, systematically
lowering the quality of gear/cash a senior veteran receives.

## Problem

`MusterOutTerm._compute_total_rolls` (`src/terms/careers/muster_out.py:234`)
correctly adds rank-based **extra rolls** (`(rank + 1) // 2`). But each
`MusterOutStep` is constructed with `dm=0` (default) — the term never passes a
benefit DM — so the Core Rulebook's **Rank 5–6 → DM +1 to all Benefit rolls**
rule is missing. `MusterOutStep` already supports a `dm` field and applies it
(`self.roll_value = self.raw_roll + self.dm`); it is simply never set.

Identified by a NotebookLM audit against Core Rulebook.pdf (Mongoose Traveller
2022, Mustering Out Benefits).

## Scope

- `src/terms/careers/muster_out.py` — in `MusterOutTerm.__init__`, compute a
  benefit DM (`+1` when `rank >= 5`, else `0`) and pass it into each
  `MusterOutStep(dm=...)`. Confirm whether the DM applies to both the Cash and
  Material columns per RAW (it applies to Benefit rolls generally) and that the
  existing index clamp still behaves at the top of the table.

## Done when

- [ ] A character mustering out at rank 5 or 6 has `dm == 1` on their
      `MusterOutStep`s; ranks 0–4 have `dm == 0`.
- [ ] A test asserts the DM shifts the resolved benefit index (seeded dice via
      `src.utilities.rng`) for a rank-5 muster-out.
- [ ] `uv run pytest` is green.

## Notes

Small and self-contained; the plumbing (`MusterOutStep.dm`) already exists.
Independent of the other fidelity items.
</content>
