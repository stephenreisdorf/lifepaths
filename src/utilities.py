import random


def roll(d: int) -> int:
    """Roll `d` six-sided dice and return the sum."""
    rolls = [random.randint(1, 6) for _ in range(d)]
    result = sum(rolls)
    return result
