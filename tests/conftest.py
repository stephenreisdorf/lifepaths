import pytest

from src import utilities


@pytest.fixture
def seeded_rng():
    """Seed the module-level RNG deterministically, restoring state afterward.

    Saving and restoring the state means seeding never leaks across tests
    regardless of execution order.
    """
    state = utilities.rng.getstate()
    utilities.rng.seed(1234)
    yield utilities.rng
    utilities.rng.setstate(state)
