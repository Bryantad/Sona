"""LRU TTL cache for AI provider responses (feature gated).

The cache is intentionally simple: dictionary + doubly-linked list ordering.
No external dependencies. Time source is injected for testability.
"""
from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..flags import get_flags


@dataclass
class _Node:
    key: Any
    value: Any
    expires_at: float
    prev: _Node | None = None
    next: _Node | None = None


class LRUCacheTTL:
    def __init__(
        self,
        max_entries: int,
        ttl_seconds: float,
        now: Callable[[], float] | None = None,
    ):
        self.max = max_entries
        self.ttl = ttl_seconds
        self.now = now or time.time
        self.map: dict[Any, _Node] = {}
        # Sentinel nodes for head/tail
        self.head = _Node("__head__", None, 0)
        self.tail = _Node("__tail__", None, 0)
        self.head.next = self.tail
        self.tail.prev = self.head
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    # Internal helpers
    def _remove(self, node: _Node) -> None:
        if node.prev:  # unlink
            node.prev.next = node.next
        if node.next:
            node.next.prev = node.prev
        node.prev = node.next = None

    def _insert_front(self, node: _Node) -> None:
        first = self.head.next
        node.next = first
        node.prev = self.head
        if first:
            first.prev = node
        self.head.next = node

    def _evict_if_needed(self) -> None:
        while len(self.map) > self.max:
            # LRU is tail.prev
            lru = self.tail.prev
            if not lru or lru is self.head:
                break
            self._remove(lru)
            self.map.pop(lru.key, None)
            self.evictions += 1

    def _expired(self, node: _Node) -> bool:
        return self.ttl > 0 and node.expires_at < self.now()

    # Public API
    def get(self, key: Any) -> Any | None:
        node = self.map.get(key)
        if not node:
            self.misses += 1
            return None
        if self._expired(node):
            self.misses += 1
            # Remove expired
            self._remove(node)
            self.map.pop(key, None)
            return None
        # Move to front
        self._remove(node)
        self._insert_front(node)
        self.hits += 1
        return node.value

    def set(self, key: Any, value: Any) -> None:
        if key in self.map:
            node = self.map[key]
            node.value = value
            node.expires_at = self.now() + self.ttl if self.ttl > 0 else 0
            self._remove(node)
            self._insert_front(node)
        else:
            node = _Node(
                key,
                value,
                self.now() + self.ttl if self.ttl > 0 else 0,
            )
            self.map[key] = node
            self._insert_front(node)
        self._evict_if_needed()

    def stats(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "size": len(self.map),
            "max": self.max,
            "ttl": self.ttl,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
        }


_global_cache: LRUCacheTTL | None = None

 
def get_cache() -> LRUCacheTTL | None:
    flags = get_flags()
    if (
        not flags.enable_cache
        or flags.cache_max_entries <= 0
        or flags.cache_ttl_seconds <= 0
    ):
        return None
    global _global_cache
    if _global_cache is None:
        _global_cache = LRUCacheTTL(
            flags.cache_max_entries, flags.cache_ttl_seconds
        )
    return _global_cache
