# Commission step for military careers

Army, Navy, and Marine careers should offer a commission roll. Nothing in `CareerTerm` (`src/terms/careers.py:435-531`) branches on this.

## Rules

- Optional to attempt.
- Success makes the Traveller a **rank 1 officer**.
- First term only, unless `SOC >= 9` (in which case any term, with `DM -1` per term after the first).
- If you gain a commission, **no advancement roll** that term.
- Failed commission → still allowed to roll for advancement.
- Advancement-DM events apply to commission rolls too.

## Scope

- Add a `CommissionRollStep` (choice to attempt, then automatic 2d6 roll).
- Insert it into `CareerTerm.advance()` between survival success and advancement for military careers.
- Flag commissioned characters (e.g. `CareerRecord.commissioned: bool`) so subsequent terms use the Officer rank track.
- Depends on Officer skill table / rank track (separate backlog item).
