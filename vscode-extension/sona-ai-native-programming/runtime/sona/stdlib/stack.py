"""Simple LIFO stack implementation."""
from __future__ import annotations

from typing import Generic, Iterable, Iterator, List, Optional, TypeVar

T = TypeVar("T")


class Stack(Generic[T]):
    def __init__(self, items: Optional[Iterable[T]] = None) -> None:
        self._items: List[T] = list(items or [])

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self) -> T:
        if not self._items:
            raise IndexError("peek from empty stack")
        return self._items[-1]

    def is_empty(self) -> bool:
        return not self._items

    def size(self) -> int:
        return len(self._items)

    def clear(self) -> None:
        self._items.clear()

    def __len__(self) -> int:  # pragma: no cover
        return len(self._items)

    def __iter__(self) -> Iterator[T]:  # pragma: no cover
        return iter(self._items)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Stack({self._items!r})"


__all__ = ["Stack"]
