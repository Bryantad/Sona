"""Random utilities for Sona programs."""

from __future__ import annotations

import random as _random
from typing import Sequence, TypeVar


T = TypeVar("T")


def random() -> float:
    return _random.random()


def randint(a: int, b: int) -> int:
    return _random.randint(a, b)


def choice(seq: Sequence[T]) -> T:
    return _random.choice(seq)


def shuffle(seq: list[T]) -> list[T]:
    _random.shuffle(seq)
    return seq


def sample(population: Sequence[T], k: int) -> list[T]:
    return _random.sample(population, k)


def uniform(a: float, b: float) -> float:
    return _random.uniform(a, b)


def seed(value: int | None = None) -> None:
    """
    Set random seed for reproducibility.
    
    Args:
        value: Seed value (None = use system time)
    
    Example:
        random.seed(42)  # Reproducible results
    """
    _random.seed(value)


def choices(population: Sequence[T], k: int = 1, weights=None) -> list[T]:
    """
    Return k selections from population (with replacement).
    
    Args:
        population: Population to choose from
        k: Number of selections
        weights: Optional weights for weighted selection
    
    Returns:
        List of k selections
    
    Example:
        items = random.choices(['a', 'b', 'c'], k=5, weights=[1, 2, 3])
    """
    return _random.choices(population, weights=weights, k=k)


def gauss(mu: float, sigma: float) -> float:
    """
    Generate random number from Gaussian distribution.
    
    Args:
        mu: Mean
        sigma: Standard deviation
    
    Returns:
        Random float from normal distribution
    
    Example:
        value = random.gauss(100, 15)  # IQ-like distribution
    """
    return _random.gauss(mu, sigma)


def triangular(low: float, high: float, mode: float | None = None) -> float:
    """
    Generate random number from triangular distribution.
    
    Args:
        low: Lower boundary
        high: Upper boundary
        mode: Peak value (None = midpoint)
    
    Returns:
        Random float
    
    Example:
        value = random.triangular(0, 100, 50)
    """
    return _random.triangular(low, high, mode)


def randbytes(n: int) -> bytes:
    """
    Generate n random bytes.
    
    Args:
        n: Number of bytes
    
    Returns:
        Random bytes
    
    Example:
        data = random.randbytes(16)
    """
    return _random.randbytes(n)


def coin_flip() -> bool:
    """
    Simulate coin flip.
    
    Returns:
        True (heads) or False (tails)
    
    Example:
        if random.coin_flip():
            print("Heads!")
    """
    return _random.random() < 0.5


def dice(sides: int = 6) -> int:
    """
    Roll a die with specified number of sides.
    
    Args:
        sides: Number of sides (default: 6)
    
    Returns:
        Random int from 1 to sides
    
    Example:
        roll = random.dice(20)  # D20
    """
    return _random.randint(1, sides)


def weighted_choice(choices: dict[T, float]) -> T:
    """
    Choose item based on weights.
    
    Args:
        choices: Dict mapping items to weights
    
    Returns:
        Weighted random choice
    
    Example:
        item = random.weighted_choice({'common': 0.7, 'rare': 0.3})
    """
    items = list(choices.keys())
    weights = list(choices.values())
    return _random.choices(items, weights=weights, k=1)[0]


__all__ = [
    "random", "randint", "choice", "shuffle", "sample", "uniform",
    "seed", "choices", "gauss", "triangular", "randbytes",
    "coin_flip", "dice", "weighted_choice"
]
