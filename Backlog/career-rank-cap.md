# Career rank is uncapped

`Character.promote` (`src/character.py:88-92`) keeps incrementing `CareerRecord.rank` past the highest entry in the YAML `ranks` list. No crash (the bonus lookup in `AdvancementRollStep._apply_rank_bonus` just no-ops when there's no matching entry), but e.g. Navy has ranks 0–6 and a character can currently reach rank 11+.

## Fix

Cap at `max(r["rank"] for r in ranks)` in `AdvancementRollStep`, or prevent further advancement rolls once the character is at max rank.
