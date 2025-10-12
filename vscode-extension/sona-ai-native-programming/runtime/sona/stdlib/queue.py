"""Simple FIFO queue implementation for Sona programs."""
from __future__ import annotations

from collections import deque
from typing import Deque, Generic, Iterable, Iterator, Optional, TypeVar

T = TypeVar("T")


class Queue(Generic[T]):
    def __init__(self, items: Optional[Iterable[T]] = None) -> None:
        self._items: Deque[T] = deque(items or [])

    def enqueue(self, item: T) -> None:
        self._items.append(item)

    def dequeue(self) -> T:
        if not self._items:
            raise IndexError("dequeue from empty queue")
        return self._items.popleft()

    def peek(self) -> T:
        if not self._items:
            raise IndexError("peek from empty queue")
        return self._items[0]

    def is_empty(self) -> bool:
        return not self._items

    def size(self) -> int:
        return len(self._items)

    def clear(self) -> None:
        self._items.clear()

    def __len__(self) -> int:  # pragma: no cover - delegated to size
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

    def __repr__(self) -> str:  # pragma: no cover - representation helper
        return f"Queue({list(self._items)!r})"


__all__ = ["Queue"]
