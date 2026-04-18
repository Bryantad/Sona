"""
heap - Heap/Priority queue for Sona stdlib

Provides heap operations:
- MinHeap/MaxHeap: Priority queue
- push/pop: Heap operations
"""

import heapq


class MinHeap:
    """Min heap implementation."""
    
    def __init__(self, items=None):
        """Initialize min heap."""
        self.heap = []
        if items:
            for item in items:
                self.push(item)
    
    def push(self, item):
        """Push item onto heap."""
        heapq.heappush(self.heap, item)
    
    def pop(self):
        """Pop smallest item."""
        if self.heap:
            return heapq.heappop(self.heap)
        return None
    
    def peek(self):
        """Peek at smallest item."""
        if self.heap:
            return self.heap[0]
        return None
    
    def size(self):
        """Get heap size."""
        return len(self.heap)
    
    def is_empty(self):
        """Check if heap is empty."""
        return len(self.heap) == 0


class MaxHeap:
    """Max heap implementation."""
    
    def __init__(self, items=None):
        """Initialize max heap."""
        self.heap = []
        if items:
            for item in items:
                self.push(item)
    
    def push(self, item):
        """Push item onto heap."""
        heapq.heappush(self.heap, -item if isinstance(item, (int, float)) else item)
    
    def pop(self):
        """Pop largest item."""
        if self.heap:
            val = heapq.heappop(self.heap)
            return -val if isinstance(val, (int, float)) else val
        return None
    
    def peek(self):
        """Peek at largest item."""
        if self.heap:
            val = self.heap[0]
            return -val if isinstance(val, (int, float)) else val
        return None
    
    def size(self):
        """Get heap size."""
        return len(self.heap)
    
    def is_empty(self):
        """Check if heap is empty."""
        return len(self.heap) == 0


def min_heap(items=None):
    """
    Create min heap.
    
    Args:
        items: Initial items
    
    Returns:
        MinHeap object
    
    Example:
        h = heap.min_heap([3, 1, 4, 1, 5])
        print(h.pop())  # 1
    """
    return MinHeap(items)


def max_heap(items=None):
    """
    Create max heap.
    
    Args:
        items: Initial items
    
    Returns:
        MaxHeap object
    
    Example:
        h = heap.max_heap([3, 1, 4, 1, 5])
        print(h.pop())  # 5
    """
    return MaxHeap(items)


def heapify(items):
    """
    Transform list into a heap in-place.
    
    Args:
        items: List to transform
    
    Example:
        arr = [3, 1, 4, 1, 5]
        heapify(arr)
        # arr is now a valid min-heap
    """
    heapq.heapify(items)
    return items


def push(heap_list, item):
    """
    Push item onto heap.
    
    Args:
        heap_list: Heap (list)
        item: Item to push
    
    Example:
        h = []
        push(h, 5)
        push(h, 2)
    """
    heapq.heappush(heap_list, item)
    return heap_list


def pop(heap_list):
    """
    Pop and return smallest item from heap.
    
    Args:
        heap_list: Heap (list)
    
    Returns:
        Smallest item or None if empty
    
    Example:
        h = [1, 3, 2]
        heapify(h)
        print(pop(h))  # 1
    """
    if heap_list:
        return heapq.heappop(heap_list)
    return None


def pushpop(heap_list, item):
    """
    Push item then pop smallest. More efficient than separate operations.
    
    Args:
        heap_list: Heap (list)
        item: Item to push
    
    Returns:
        Smallest item after push
    
    Example:
        h = [2, 3, 4]
        heapify(h)
        print(pushpop(h, 1))  # 1
    """
    if heap_list:
        return heapq.heappushpop(heap_list, item)
    return item


def replace(heap_list, item):
    """
    Pop smallest item then push new item. More efficient than separate operations.
    
    Args:
        heap_list: Heap (list)
        item: Item to push
    
    Returns:
        The popped item
    
    Example:
        h = [2, 3, 4]
        heapify(h)
        print(replace(h, 5))  # 2
    """
    if heap_list:
        return heapq.heapreplace(heap_list, item)
    return None


def nsmallest(n, items, key=None):
    """
    Find n smallest elements.
    
    Args:
        n: Number of items
        items: Iterable
        key: Optional key function
    
    Returns:
        List of n smallest items
    
    Example:
        print(nsmallest(3, [5, 2, 8, 1, 9]))  # [1, 2, 5]
    """
    return heapq.nsmallest(n, items, key=key)


def nlargest(n, items, key=None):
    """
    Find n largest elements.
    
    Args:
        n: Number of items
        items: Iterable
        key: Optional key function
    
    Returns:
        List of n largest items
    
    Example:
        print(nlargest(3, [5, 2, 8, 1, 9]))  # [9, 8, 5]
    """
    return heapq.nlargest(n, items, key=key)


def merge(*iterables, key=None, reverse=False):
    """
    Merge multiple sorted iterables into single sorted iterable.
    
    Args:
        iterables: Multiple sorted iterables
        key: Optional key function
        reverse: Reverse order
    
    Returns:
        List of merged sorted items
    
    Example:
        print(merge([1, 3, 5], [2, 4, 6]))  # [1, 2, 3, 4, 5, 6]
    """
    return list(heapq.merge(*iterables, key=key, reverse=reverse))


def peek(heap_list):
    """
    Peek at smallest item without removing.
    
    Args:
        heap_list: Heap (list)
    
    Returns:
        Smallest item or None if empty
    
    Example:
        h = [1, 3, 2]
        heapify(h)
        print(peek(h))  # 1 (still in heap)
    """
    if heap_list:
        return heap_list[0]
    return None


__all__ = [
    "MinHeap",
    "MaxHeap",
    "min_heap",
    "max_heap",
    "heapify",
    "push",
    "pop",
    "pushpop",
    "replace",
    "nsmallest",
    "nlargest",
    "merge",
    "peek",
]
