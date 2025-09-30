"""Random helpers wrapping Python's :mod:`random`."""

from __future__ import annotations

import os
import random as _random
from typing import Iterable, Sequence, TypeVar


T = TypeVar("T")


class RandomModule:
    def __init__(self) -> None:
        self._rng = _random.Random()

    def random(self) -> float:
        return self._rng.random()

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(int(a), int(b))

    def choice(self, items: Sequence[T]) -> T | None:
        if not items:
            return None
        return self._rng.choice(items)

    def shuffle(self, items: Iterable[T]) -> list[T]:
        items_list = list(items)
        self._rng.shuffle(items_list)
        return items_list

    def seed(self, value: int | float | None = None) -> None:
        self._rng.seed(value)


random = RandomModule()
__all__ = ["random"]


if (
    os.environ.get("SONA_DEBUG") == "1"
    and os.environ.get("SONA_MODULE_SILENT") != "1"
):
    print("[DEBUG] random module loaded")
