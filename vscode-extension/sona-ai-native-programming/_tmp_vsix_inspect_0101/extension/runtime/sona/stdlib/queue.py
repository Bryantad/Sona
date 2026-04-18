"""Enhanced FIFO queue implementation with priority and advanced operations."""
from __future__ import annotations

from collections import deque
from typing import (
    Any, Callable, Deque, Generic, Iterable, Iterator, List, Optional, TypeVar
)
import heapq

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
    
    def to_list(self) -> List[T]:
        """Convert queue to list (front to back)."""
        return list(self._items)
    
    def contains(self, item: T) -> bool:
        """Check if item exists in queue."""
        return item in self._items
    
    def copy(self) -> "Queue[T]":
        """Create a shallow copy of the queue."""
        return Queue(self._items.copy())


class PriorityQueue(Generic[T]):
    """Priority queue implementation (lower priority value = higher priority)."""
    
    def __init__(self) -> None:
        self._heap: List[tuple[Any, int, T]] = []
        self._counter = 0
    
    def enqueue(self, item: T, priority: float = 0) -> None:
        """Add item with priority."""
        heapq.heappush(self._heap, (priority, self._counter, item))
        self._counter += 1
    
    def dequeue(self) -> T:
        """Remove and return highest priority item."""
        if not self._heap:
            raise IndexError("dequeue from empty queue")
        return heapq.heappop(self._heap)[2]
    
    def peek(self) -> T:
        """Return highest priority item without removing."""
        if not self._heap:
            raise IndexError("peek from empty queue")
        return self._heap[0][2]
    
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return not self._heap
    
    def size(self) -> int:
        """Get number of items."""
        return len(self._heap)
    
    def clear(self) -> None:
        """Remove all items."""
        self._heap.clear()
        self._counter = 0


def create(items: Optional[Iterable[Any]] = None) -> Queue[Any]:
    """
    Create a new FIFO queue.
    
    Args:
        items: Optional initial items
        
    Returns:
        New Queue instance
        
    Example:
        >>> q = queue.create([1, 2, 3])
        >>> q.dequeue()  # Returns 1
        >>> q.peek()  # Returns 2
    """
    return Queue(items)


def create_priority() -> PriorityQueue[Any]:
    """
    Create a new priority queue.
    
    Returns:
        New PriorityQueue instance
        
    Example:
        >>> pq = queue.create_priority()
        >>> pq.enqueue("low", priority=10)
        >>> pq.enqueue("high", priority=1)
        >>> pq.dequeue()  # Returns "high"
    """
    return PriorityQueue()


def enqueue(queue: Queue[T], item: T) -> None:
    """Add item to back of queue."""
    queue.enqueue(item)


def dequeue(queue: Queue[T]) -> T:
    """Remove and return front item."""
    return queue.dequeue()


def peek(queue: Queue[T]) -> T:
    """Return front item without removing."""
    return queue.peek()


def is_empty(queue: Queue[Any]) -> bool:
    """Check if queue is empty."""
    return queue.is_empty()


def size(queue: Queue[Any]) -> int:
    """Get number of items in queue."""
    return queue.size()


def clear(queue: Queue[Any]) -> None:
    """Remove all items from queue."""
    queue.clear()


def to_list(queue: Queue[T]) -> List[T]:
    """Convert queue to list (front to back)."""
    return queue.to_list()


def from_list(items: List[Any]) -> Queue[Any]:
    """Create queue from list."""
    return Queue(items)


def reverse(queue: Queue[T]) -> Queue[T]:
    """Create new queue with reversed order."""
    return Queue(reversed(queue.to_list()))


def filter_queue(queue: Queue[T], predicate: Callable[[T], bool]) -> Queue[T]:
    """Create new queue with items matching predicate."""
    return Queue([item for item in queue if predicate(item)])


def map_queue(queue: Queue[T], func: Callable[[T], Any]) -> Queue[Any]:
    """Create new queue with function applied to each item."""
    return Queue([func(item) for item in queue])


def merge_queues(*queues: Queue[T]) -> Queue[T]:
    """
    Merge multiple queues into one.
    
    Args:
        queues: Queues to merge
    
    Returns:
        New queue with all items
    
    Example:
        merged = queue.merge_queues(q1, q2, q3)
    """
    result = Queue()
    for q in queues:
        for item in q:
            result.enqueue(item)
    return result


def batch_dequeue(queue: Queue[T], count: int) -> List[T]:
    """
    Dequeue multiple items at once.
    
    Args:
        queue: Queue to dequeue from
        count: Number of items to dequeue
    
    Returns:
        List of dequeued items
    
    Example:
        items = queue.batch_dequeue(q, 5)
    """
    result = []
    for _ in range(min(count, queue.size())):
        result.append(queue.dequeue())
    return result


def drain(queue: Queue[T]) -> List[T]:
    """
    Remove and return all items from queue.
    
    Args:
        queue: Queue to drain
    
    Returns:
        List of all items
    
    Example:
        all_items = queue.drain(q)
    """
    result = []
    while not queue.is_empty():
        result.append(queue.dequeue())
    return result


__all__ = [
    "Queue", "PriorityQueue", "create", "create_priority",
    "enqueue", "dequeue", "peek", "is_empty", "size", "clear",
    "to_list", "from_list", "reverse", "filter_queue", "map_queue",
    "merge_queues", "batch_dequeue", "drain"
]
