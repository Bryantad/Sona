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


__all__ = ["random", "randint", "choice", "shuffle", "sample", "uniform"]
