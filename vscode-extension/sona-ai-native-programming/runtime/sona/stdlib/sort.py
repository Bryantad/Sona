"""Sorting helpers for Sona programs."""
from __future__ import annotations

from typing import Iterable, List, Sequence, TypeVar, Callable, Optional
import heapq

T = TypeVar("T")


def quicksort(sequence: Iterable[T], *, key: Optional[Callable[[T], T]] = None) -> list[T]:
    """Return a new list containing *sequence* sorted using quicksort.

    A ``key`` function can be provided; it behaves like ``sorted``.
    """

    data = list(sequence)
    if len(data) <= 1:
        return data

    keyfunc = key if key is not None else lambda x: x
    pivot = data[len(data) // 2]
    left = [item for item in data if keyfunc(item) < keyfunc(pivot)]
    middle = [item for item in data if keyfunc(item) == keyfunc(pivot)]
    right = [item for item in data if keyfunc(item) > keyfunc(pivot)]
    return quicksort(left, key=keyfunc) + middle + quicksort(right, key=keyfunc)


def mergesort(sequence: Iterable[T], *, key: Optional[Callable[[T], T]] = None) -> list[T]:
    data = list(sequence)
    if len(data) <= 1:
        return data

    keyfunc = key if key is not None else lambda x: x

    def merge(left: List[T], right: List[T]) -> List[T]:
        result: List[T] = []
        i = j = 0
        while i < len(left) and j < len(right):
            if keyfunc(left[i]) <= keyfunc(right[j]):
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        result.extend(left[i:])
        result.extend(right[j:])
        return result

    mid = len(data) // 2
    left = mergesort(data[:mid], key=keyfunc)
    right = mergesort(data[mid:], key=keyfunc)
    return merge(left, right)


def top_k(sequence: Iterable[T], k: int, *, key: Optional[Callable[[T], T]] = None) -> list[T]:
    """Return the ``k`` largest items from *sequence* preserving order."""

    if k < 0:
        raise ValueError("k must be non-negative")
    keyfunc = key if key is not None else None
    return heapq.nlargest(k, sequence, key=keyfunc)


__all__ = ["quicksort", "mergesort", "top_k"]
