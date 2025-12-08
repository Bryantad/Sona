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


def partition(iterable: Iterable[T], predicate: Callable[[T], bool]) -> tuple[list[T], list[T]]:
    """Partition items into two lists based on predicate.
    
    Returns (truthy, falsy) tuple of lists.
    
    Example:
        partition([1, 2, 3, 4], lambda x: x % 2 == 0)
        # Returns ([2, 4], [1, 3])
    """
    truthy: list[T] = []
    falsy: list[T] = []
    for item in iterable:
        if predicate(item):
            truthy.append(item)
        else:
            falsy.append(item)
    return (truthy, falsy)


def zip_with(*iterables: Iterable[T]) -> list[tuple]:
    """Zip multiple iterables into list of tuples.
    
    Example:
        zip_with([1, 2], ['a', 'b'])
        # Returns [(1, 'a'), (2, 'b')]
    """
    return list(zip(*iterables))


def interleave(*iterables: Iterable[T]) -> list[T]:
    """Interleave items from multiple iterables.
    
    Example:
        interleave([1, 2, 3], ['a', 'b', 'c'])
        # Returns [1, 'a', 2, 'b', 3, 'c']
    """
    result: list[T] = []
    iterators = [iter(it) for it in iterables]
    while iterators:
        for it in list(iterators):
            try:
                result.append(next(it))
            except StopIteration:
                iterators.remove(it)
    return result


def compact(iterable: Iterable[T | None]) -> list[T]:
    """Remove None values from iterable.
    
    Example:
        compact([1, None, 2, None, 3])
        # Returns [1, 2, 3]
    """
    return [item for item in iterable if item is not None]


def pluck(iterable: Iterable[dict], key: str) -> list:
    """Extract values for a key from list of dicts.
    
    Example:
        pluck([{'name': 'Alice'}, {'name': 'Bob'}], 'name')
        # Returns ['Alice', 'Bob']
    """
    return [item.get(key) for item in iterable if isinstance(item, dict)]


def find(iterable: Iterable[T], predicate: Callable[[T], bool]) -> T | None:
    """Find first item matching predicate.
    
    Example:
        find([1, 2, 3, 4], lambda x: x > 2)
        # Returns 3
    """
    for item in iterable:
        if predicate(item):
            return item
    return None


def find_index(seq: Sequence[T], predicate: Callable[[T], bool]) -> int:
    """Find index of first item matching predicate.
    
    Returns -1 if not found.
    
    Example:
        find_index([1, 2, 3, 4], lambda x: x > 2)
        # Returns 2
    """
    for i, item in enumerate(seq):
        if predicate(item):
            return i
    return -1


def nth(seq: Sequence[T], index: int, default: T | None = None) -> T | None:
    """Get nth element with safe bounds checking.
    
    Example:
        nth([1, 2, 3], 1)  # Returns 2
        nth([1, 2, 3], 10, default=0)  # Returns 0
    """
    try:
        return seq[index]
    except (IndexError, KeyError):
        return default


def slice_seq(seq: Sequence[T], start: int = 0, end: int | None = None, step: int = 1) -> list[T]:
    """Slice sequence with explicit parameters.
    
    Example:
        slice_seq([1, 2, 3, 4, 5], 1, 4)
        # Returns [2, 3, 4]
    """
    return list(seq[start:end:step])


def rotate(seq: Sequence[T], n: int) -> list[T]:
    """Rotate sequence n positions.
    
    Positive n rotates right, negative rotates left.
    
    Example:
        rotate([1, 2, 3, 4], 1)  # Returns [4, 1, 2, 3]
        rotate([1, 2, 3, 4], -1)  # Returns [2, 3, 4, 1]
    """
    if not seq:
        return []
    n = n % len(seq)
    return list(seq[-n:]) + list(seq[:-n]) if n else list(seq)


def shuffle(seq: Sequence[T]) -> list[T]:
    """Return shuffled copy of sequence.
    
    Example:
        shuffle([1, 2, 3, 4])
        # Returns randomized list like [3, 1, 4, 2]
    """
    import random
    result = list(seq)
    random.shuffle(result)
    return result


def sample(seq: Sequence[T], k: int) -> list[T]:
    """Return k random items from sequence.
    
    Example:
        sample([1, 2, 3, 4, 5], 2)
        # Returns 2 random items like [3, 1]
    """
    import random
    return random.sample(list(seq), k)


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
    # advanced
    "partition",
    "zip_with",
    "interleave",
    "compact",
    "pluck",
    "find",
    "find_index",
    "nth",
    "slice_seq",
    "rotate",
    "shuffle",
    "sample",
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
