"""Muster-out benefit rolls: rank-based extra rolls and the Rank 5–6 DM.

Reaching rank 5 or 6 grants +1 DM on every Benefit roll (Core Rulebook,
Mustering Out Benefits). These tests pin the per-step DM and show that the
DM shifts the resolved benefit index for a senior veteran.
"""

import pytest

from src import utilities
from src.character import Character
from src.terms.careers import MusterOutTerm

# A 7-long cash column so a 1d6 (+1 DM) never clamps at the table top,
# letting us observe the DM shifting the resolved index cleanly.
_CASH = [1000, 2000, 5000, 10000, 20000, 50000, 100000]
_BENEFITS = {"cash": _CASH, "material": ["Weapon", "Contact"]}


@pytest.mark.parametrize(
    "rank, expected_dm",
    [(0, 0), (1, 0), (4, 0), (5, 1), (6, 1)],
)
def test_benefit_dm_only_for_senior_ranks(rank, expected_dm):
    term = MusterOutTerm(
        Character(name="T", characteristics={}, skills={}),
        career_name="Army",
        benefits=_BENEFITS,
        terms_served=2,
        rank=rank,
    )
    assert term.benefit_dm == expected_dm
    assert all(step.dm == expected_dm for step in term.steps)


def _first_cash_index(rank: int) -> int:
    """Resolve the first Cash benefit roll for a muster-out at ``rank``,
    seeding the RNG identically so the raw 1d6 is the same across ranks."""
    utilities.rng.seed(99)
    term = MusterOutTerm(
        Character(name="T", characteristics={}, skills={}),
        career_name="Army",
        benefits=_BENEFITS,
        terms_served=1,
        rank=rank,
    )
    step = term.steps[0]
    step.resolve({"selections": [step.CASH]})
    step.apply()
    return step.outcome.data["index"]


def test_rank5_dm_shifts_resolved_benefit_index(seeded_rng):
    """The +1 DM at rank 5 lands one row higher on the benefit table than
    the identical roll would at rank 4 (no clamping in the 7-long column)."""
    idx_rank4 = _first_cash_index(4)
    idx_rank5 = _first_cash_index(5)
    assert idx_rank5 == idx_rank4 + 1
