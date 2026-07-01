import random

# Module-level RNG. Production uses it unseeded (system entropy); tests call
# rng.seed(...) for deterministic dice. Isolating our own Random instance keeps
# us off the global random module's shared state.
rng = random.Random()


def roll(d: int) -> int:
    """Roll `d` six-sided dice and return the sum."""
    return sum(rng.randint(1, 6) for _ in range(d))
