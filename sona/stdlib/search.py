"""Search helpers for Sona programs."""
from __future__ import annotations

from typing import Iterable, Sequence, TypeVar

T = TypeVar("T")


def linear_search(sequence: Iterable[T], target: T) -> int:
    """Return the index of *target* in *sequence* using linear scan.

    Returns ``-1`` when the value is missing.
    """

    for index, value in enumerate(sequence):
        if value == target:
            return index
    return -1


def binary_search(sequence: Sequence[T], target: T) -> int:
    """Return the index of *target* in a sorted *sequence*.

    The sequence **must** be sorted in ascending order. Returns ``-1`` when the
    element is absent.
    """

    lo = 0
    hi = len(sequence) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        value = sequence[mid]
        if value == target:
            return mid
        if value < target:  # type: ignore[operator]
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def find_all(sequence: Iterable[T], target: T) -> list[int]:
    """Return a list of all indices where *target* appears."""

    return [idx for idx, value in enumerate(sequence) if value == target]


__all__ = ["linear_search", "binary_search", "find_all"]
