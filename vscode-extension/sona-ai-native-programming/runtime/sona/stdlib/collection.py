"""Sona standard library: collections helpers.

This module provides high level helpers around Python's built-in collection
types.  Every function returns plain Python objects so they can be consumed
directly by Sona programs without additional adapters.
"""

from collections import Counter, deque
from itertools import chain, islice
from typing import Callable, Dict, Iterable, List, Sequence, TypeVar


T = TypeVar("T")


def len(obj: Sequence[T]) -> int:
    """Return the length of a sequence (alias for :func:`len`)."""

    return __builtins__["len"](obj)


def range(start: int, end: int | None = None, step: int = 1) -> list[int]:
    """Return a materialised list of numbers.

    Mirrors the behaviour of Python's :func:`range` but returns a list so that
    Sona programs receive a concrete sequence they can iterate multiple times.
    """

    if end is None:
        return list(__builtins__["range"](start))
    return list(__builtins__["range"](start, end, step))


def first(seq: Sequence[T], default: T | None = None) -> T | None:
    """Return the first element of *seq* or *default* when empty."""

    return seq[0] if seq else default


def last(seq: Sequence[T], default: T | None = None) -> T | None:
    """Return the last element of *seq* or *default* when empty."""

    return seq[-1] if seq else default


def take(seq: Sequence[T], count: int) -> list[T]:
    """Return the first *count* items from the sequence as a new list."""

    if count <= 0:
        return []
    return list(islice(seq, count))


def drop(seq: Sequence[T], count: int) -> list[T]:
    """Return a list without the first *count* items from the sequence."""

    if count <= 0:
        return list(seq)
    return list(seq[count:])


def flatten(iterables: Iterable[Iterable[T]]) -> list[T]:
    """Flatten one level of nesting and return a list."""

    return list(chain.from_iterable(iterables))


def unique(iterable: Iterable[T]) -> list[T]:
    """Return unique elements preserving first-seen order."""

    seen: set[T] = set()
    result: list[T] = []
    for item in iterable:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def frequencies(iterable: Iterable[T]) -> dict[T, int]:
    """Return a frequency map for items in *iterable*."""

    return dict(Counter(iterable))


def push(seq: list[T], value: T) -> list[T]:
    """Append *value* to *seq* and return the list for chaining."""

    seq.append(value)
    return seq


def pop(seq: list[T], index: int | None = None):
    """Remove and return an item from *seq* (default last)."""

    if index is None:
        return seq.pop()
    return seq.pop(index)


def deque_push_left(queue: deque[T], value: T) -> deque[T]:
    """Push *value* to the left side of a deque."""

    queue.appendleft(value)
    return queue


def deque_push(queue: deque[T], value: T) -> deque[T]:
    """Push *value* to the right side of a deque."""

    queue.append(value)
    return queue


def deque_pop_left(queue: deque[T]) -> T:
    """Remove and return the item from the left side of a deque."""

    return queue.popleft()


def deque_pop(queue: deque[T]) -> T:
    """Remove and return the item from the right side of a deque."""

    return queue.pop()


__all__ = [
    "len",
    "range",
    "first",
    "last",
    "take",
    "drop",
    "flatten",
    "unique",
    "unique_by",
    "chunk",
    "group_by",
    "frequencies",
    "push",
    "pop",
    "deque_push_left",
    "deque_push",
    "deque_pop_left",
    "deque_pop",
]


def chunk(iterable: Iterable[T], size: int) -> List[List[T]]:
    """Split *iterable* into consecutive lists of length up to *size*.

    - Preserves input order
    - Returns a concrete list of lists for easy consumption in Sona
    - Raises ValueError when size <= 0
    """

    if size <= 0:
        raise ValueError("size must be a positive integer")
    bucket: List[T] = []
    out: List[List[T]] = []
    for item in iterable:
        bucket.append(item)
        if len(bucket) >= size:
            out.append(bucket)
            bucket = []
    if bucket:
        out.append(bucket)
    return out


def unique_by(iterable: Iterable[T], key: Callable[[T], T | object] | None = None) -> List[T]:
    """Return unique elements using an optional key function, preserving order.

    - The first occurrence for a given key value is kept
    - When key is None, behaves like :func:`unique`
    """

    if key is None:
        return unique(iterable)
    seen: set[object] = set()
    out: List[T] = []
    for item in iterable:
        k = key(item)
        if k in seen:
            continue
        seen.add(k)
        out.append(item)
    return out


def group_by(iterable: Iterable[T], key: Callable[[T], object]) -> Dict[object, List[T]]:
    """Group items by ``key(item)`` preserving order of first occurrence.

    Returns an insertion-ordered dict mapping key -> list of items.
    """

    result: Dict[object, List[T]] = {}
    for item in iterable:
        k = key(item)
        bucket = result.get(k)
        if bucket is None:
            bucket = []
            result[k] = bucket
        bucket.append(item)
    return result
