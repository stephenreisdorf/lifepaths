from src import utilities
from src.utilities import roll


def test_roll_within_range(seeded_rng):
    for _ in range(50):
        assert 2 <= roll(2) <= 12


def test_roll_single_die_range(seeded_rng):
    for _ in range(50):
        assert 1 <= roll(1) <= 6


def test_same_seed_reproduces_sequence():
    utilities.rng.seed(42)
    first = [roll(2) for _ in range(10)]
    utilities.rng.seed(42)
    second = [roll(2) for _ in range(10)]
    assert first == second
