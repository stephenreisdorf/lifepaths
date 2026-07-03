# Pre-career education (University / Academy) diverges from the Core Rulebook

Several University and Military Academy numbers and check-characteristics do not
match the official pre-career education rules. Because education feeds directly
into the first career (skills, EDU, and a qualification DM), these errors ripple
into the rest of creation.

## Problem

Measured against Core Rulebook.pdf (Mongoose Traveller 2022, pre-career
education) via a NotebookLM audit. Data lives in `src/terms/education/config.py`;
resolution in `src/terms/education/steps.py` / `terms.py`.

**University** (`config.py` `UNIVERSITY`):
- Entry target is **7**; RAW is **6+**.
- Entry bonus is **+1 DM if INT ≥ 9**; RAW is **+1 DM if SOC ≥ 9** (and RAW also
  applies **−1 DM in term 2, −2 in term 3** entry penalties, not modelled).
- Graduation rolls against **Education**; RAW graduation is an **Intelligence**
  check.
- Honours grants **EDU +2**; RAW grants **EDU +1 plus a Commission roll**.
- The graduate qualification DM (+2) is applied to **any** first career; RAW
  restricts the graduation DM to **specific careers** only.

**Military Academy** (`config.py` `MILITARY_ACADEMIES`):
- Requires a characteristic minimum to **apply** (INT/END ≥ 6); RAW lists **no
  application threshold**.
- Graduation rolls against **Education** vs 7; RAW graduation is an
  **Intelligence 7+** check (with +1 DM if END ≥ 8, +1 DM if SOC ≥ 8).
- Missing term-based entry penalties (**−2 term 2, −4 term 3**).
- Honours grants **EDU +1**; RAW grants **EDU +1 AND SOC +1**.

## Scope

- `src/terms/education/config.py` — correct targets, bonus characteristics,
  honours effects, and the graduation check characteristic for both institutions.
- `src/terms/education/steps.py` — `UniversityGraduationStep` /
  `AcademyGraduationStep` currently key their graduation roll and honours bumps
  off Education; switch to Intelligence and apply the correct honours effects
  (University honours → Commission roll; Academy honours → SOC +1).
- Decide scope for the not-yet-modelled bits: term-based entry penalties, and the
  "graduation DM applies to specific careers only" restriction. These can be a
  follow-up if too large — capture explicitly which are in/out.

## Done when

- [ ] University entry target is 6, with +1 DM keyed on SOC ≥ 9 (not INT).
- [ ] University graduation is an INT check; honours grants EDU +1 (+ a Commission
      roll or an explicit TODO note if deferred).
- [ ] Academy graduation is an INT 7+ check; honours grants EDU +1 and SOC +1.
- [ ] `tests/test_education.py` pins the corrected targets, check characteristics,
      and honours effects for University and all three academies.
- [ ] `uv run pytest` is green.

## Notes

Some of these read as "wrong edition" (the code blends Mongoose 1e/2e
conventions) rather than "wrong math" — reconcile against the exact rulebook in
use before landing each number. Related fidelity items: [aging](aging-official-table.md),
[characteristic-dm-zero](characteristic-dm-zero.md).
</content>
