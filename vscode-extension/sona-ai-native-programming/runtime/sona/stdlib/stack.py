"""Enhanced LIFO stack implementation with advanced operations."""
from __future__ import annotations

from typing import Any, Callable, Generic, Iterable, Iterator, List, Optional, TypeVar

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
    
    def to_list(self) -> List[T]:
        """Convert stack to list (top to bottom)."""
        return list(reversed(self._items))
    
    def contains(self, item: T) -> bool:
        """Check if item exists in stack."""
        return item in self._items
    
    def search(self, item: T) -> int:
        """
        Search for item and return distance from top.
        Returns -1 if not found.
        """
        try:
            return len(self._items) - 1 - self._items.index(item)
        except ValueError:
            return -1
    
    def copy(self) -> "Stack[T]":
        """Create a shallow copy of the stack."""
        return Stack(self._items.copy())


def create(items: Optional[Iterable[Any]] = None) -> Stack[Any]:
    """
    Create a new stack.
    
    Args:
        items: Optional initial items (bottom to top order)
        
    Returns:
        New Stack instance
        
    Example:
        >>> s = stack.create([1, 2, 3])
        >>> s.pop()  # Returns 3
        >>> s.peek()  # Returns 2
    """
    return Stack(items)


def from_list(items: List[Any]) -> Stack[Any]:
    """
    Create stack from list (list order becomes bottom to top).
    
    Args:
        items: List of items
        
    Returns:
        New Stack instance
    """
    return Stack(items)


def push(stack: Stack[T], item: T) -> None:
    """
    Push item onto stack.
    
    Args:
        stack: Stack instance
        item: Item to push
    """
    stack.push(item)


def pop(stack: Stack[T]) -> T:
    """
    Pop and return top item.
    
    Args:
        stack: Stack instance
        
    Returns:
        Top item
        
    Raises:
        IndexError: If stack is empty
    """
    return stack.pop()


def peek(stack: Stack[T]) -> T:
    """
    Return top item without removing it.
    
    Args:
        stack: Stack instance
        
    Returns:
        Top item
        
    Raises:
        IndexError: If stack is empty
    """
    return stack.peek()


def is_empty(stack: Stack[Any]) -> bool:
    """
    Check if stack is empty.
    
    Args:
        stack: Stack instance
        
    Returns:
        True if empty, False otherwise
    """
    return stack.is_empty()


def size(stack: Stack[Any]) -> int:
    """
    Get number of items in stack.
    
    Args:
        stack: Stack instance
        
    Returns:
        Number of items
    """
    return stack.size()


def clear(stack: Stack[Any]) -> None:
    """
    Remove all items from stack.
    
    Args:
        stack: Stack instance
    """
    stack.clear()


def to_list(stack: Stack[T]) -> List[T]:
    """
    Convert stack to list (top to bottom order).
    
    Args:
        stack: Stack instance
        
    Returns:
        List with top item first
    """
    return stack.to_list()


def reverse(stack: Stack[T]) -> Stack[T]:
    """
    Create new stack with reversed order.
    
    Args:
        stack: Stack instance
        
    Returns:
        New stack with reversed items
    """
    return Stack(stack.to_list())


def filter_stack(stack: Stack[T], predicate: Callable[[T], bool]) -> Stack[T]:
    """
    Create new stack with items matching predicate.
    
    Args:
        stack: Stack instance
        predicate: Function to test each item
        
    Returns:
        New stack with filtered items
    """
    return Stack([item for item in stack if predicate(item)])


def map_stack(stack: Stack[T], func: Callable[[T], Any]) -> Stack[Any]:
    """
    Create new stack with function applied to each item.
    
    Args:
        stack: Stack instance
        func: Function to apply
        
    Returns:
        New stack with transformed items
    """
    return Stack([func(item) for item in stack])


__all__ = ["Stack", "create", "from_list", "push", "pop", "peek", "is_empty", 
           "size", "clear", "to_list", "reverse", "filter_stack", "map_stack"]
