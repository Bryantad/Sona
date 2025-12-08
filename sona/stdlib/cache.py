"""
cache - Enhanced caching layer for Sona stdlib

Provides in-memory caching with advanced features:
- Cache: Cache instance with TTL
- LRU, LFU eviction policies
- Statistics and monitoring
- Batch operations
"""

import time
from typing import Any, Optional, Callable, List, Dict, Tuple
from collections import OrderedDict
from threading import Lock


class CacheEntry:
    """Single cache entry with TTL and access tracking."""
    
    def __init__(self, value, ttl=None):
        self.value = value
        self.created_at = time.time()
        self.last_accessed = self.created_at
        self.access_count = 0
        self.ttl = ttl
    
    def is_expired(self):
        """Check if entry has expired."""
        if self.ttl is None:
            return False
        return (time.time() - self.created_at) > self.ttl
    
    def access(self):
        """Record an access to this entry."""
        self.last_accessed = time.time()
        self.access_count += 1


class Cache:
    """In-memory cache with TTL support and advanced features."""
    
    def __init__(self, default_ttl=None, max_size=None, eviction_policy='lru'):
        """
        Create cache instance.
        
        Args:
            default_ttl: Default TTL in seconds (None = no expiration)
            max_size: Maximum cache size (None = unlimited)
            eviction_policy: 'lru' or 'lfu' (default: 'lru')
        """
        self._store = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.eviction_policy = eviction_policy
        self._hits = 0
        self._misses = 0
        self._lock = Lock()
    
    def _evict_one(self):
        """Evict one entry based on eviction policy."""
        if not self._store:
            return
        
        if self.eviction_policy == 'lru':
            # Least Recently Used
            oldest_key = min(self._store.keys(), 
                           key=lambda k: self._store[k].last_accessed)
            del self._store[oldest_key]
        elif self.eviction_policy == 'lfu':
            # Least Frequently Used
            least_used = min(self._store.keys(),
                           key=lambda k: self._store[k].access_count)
            del self._store[least_used]
    
    def get(self, key, default=None):
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if not found
        
        Returns:
            Cached value or default
        
        Example:
            value = cache.get("user:123")
        """
        with self._lock:
            if key in self._store:
                entry = self._store[key]
                if entry.is_expired():
                    del self._store[key]
                    self._misses += 1
                    return default
                entry.access()
                self._hits += 1
                return entry.value
            self._misses += 1
            return default
    
    def set(self, key, value, ttl=None):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (None = use default)
        
        Example:
            cache.set("user:123", user_data, ttl=3600)
        """
        with self._lock:
            # Evict if needed
            if self.max_size and len(self._store) >= self.max_size:
                if key not in self._store:  # Only evict if adding new
                    self._evict_one()
            
            if ttl is None:
                ttl = self.default_ttl
            self._store[key] = CacheEntry(value, ttl)
    
    def delete(self, key):
        """Delete key from cache."""
        if key in self._store:
            del self._store[key]
    
    def clear(self):
        """Clear all cache entries."""
        self._store = {}
    
    def cleanup(self):
        """Remove expired entries."""
        expired_keys = [
            key for key, entry in self._store.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self._store[key]
        return len(expired_keys)
    
    def has(self, key):
        """Check if key exists and is not expired."""
        return self.get(key) is not None
    
    def size(self):
        """Get number of cached items."""
        self.cleanup()
        return len(self._store)
    
    def get_or_set(self, key, factory, ttl=None):
        """
        Get value or compute and cache it.
        
        Args:
            key: Cache key
            factory: Callable to compute value if not cached
            ttl: TTL in seconds
        
        Returns:
            Cached or computed value
        
        Example:
            value = cache.get_or_set("data", lambda: expensive_computation())
        """
        value = self.get(key)
        if value is None:
            value = factory()
            self.set(key, value, ttl)
        return value
    
    def increment(self, key, delta=1, default=0):
        """
        Increment numeric value.
        
        Args:
            key: Cache key
            delta: Amount to increment
            default: Initial value if key doesn't exist
        
        Returns:
            New value
        
        Example:
            count = cache.increment("visits")
        """
        with self._lock:
            value = self.get(key)
            if value is None:
                value = default
            new_value = value + delta
            self.set(key, new_value)
            return new_value
    
    def decrement(self, key, delta=1, default=0):
        """
        Decrement numeric value.
        
        Args:
            key: Cache key
            delta: Amount to decrement
            default: Initial value if key doesn't exist
        
        Returns:
            New value
        """
        return self.increment(key, -delta, default)
    
    def get_many(self, keys):
        """
        Get multiple values.
        
        Args:
            keys: List of cache keys
        
        Returns:
            Dict of key-value pairs (only existing keys)
        
        Example:
            data = cache.get_many(["user:1", "user:2", "user:3"])
        """
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result
    
    def set_many(self, items, ttl=None):
        """
        Set multiple values.
        
        Args:
            items: Dict of key-value pairs
            ttl: TTL in seconds
        
        Example:
            cache.set_many({"user:1": data1, "user:2": data2})
        """
        for key, value in items.items():
            self.set(key, value, ttl)
    
    def delete_many(self, keys):
        """
        Delete multiple keys.
        
        Args:
            keys: List of cache keys
        
        Returns:
            Number of keys deleted
        """
        count = 0
        for key in keys:
            if key in self._store:
                del self._store[key]
                count += 1
        return count
    
    def delete_pattern(self, pattern):
        """
        Delete keys matching pattern.
        
        Args:
            pattern: String pattern (supports * wildcard)
        
        Returns:
            Number of keys deleted
        
        Example:
            cache.delete_pattern("user:*")
        """
        import re
        regex_pattern = pattern.replace('*', '.*')
        regex = re.compile(f"^{regex_pattern}$")
        
        matching_keys = [key for key in self._store.keys() if regex.match(str(key))]
        return self.delete_many(matching_keys)
    
    def keys(self, pattern=None):
        """
        Get all cache keys.
        
        Args:
            pattern: Optional pattern to filter keys
        
        Returns:
            List of cache keys
        
        Example:
            all_keys = cache.keys()
            user_keys = cache.keys("user:*")
        """
        self.cleanup()
        
        if pattern is None:
            return list(self._store.keys())
        
        import re
        regex_pattern = pattern.replace('*', '.*')
        regex = re.compile(f"^{regex_pattern}$")
        return [key for key in self._store.keys() if regex.match(str(key))]
    
    def exists(self, key):
        """
        Check if key exists (alias for has).
        
        Args:
            key: Cache key
        
        Returns:
            True if key exists and is not expired
        """
        return self.has(key)
    
    def ttl(self, key):
        """
        Get remaining TTL for key.
        
        Args:
            key: Cache key
        
        Returns:
            Remaining seconds or None if no TTL or key doesn't exist
        
        Example:
            remaining = cache.ttl("session:123")
        """
        if key not in self._store:
            return None
        
        entry = self._store[key]
        if entry.ttl is None:
            return None
        
        elapsed = time.time() - entry.created_at
        remaining = entry.ttl - elapsed
        return max(0, remaining)
    
    def stats(self):
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats
        
        Example:
            stats = cache.stats()
            print(f"Hit rate: {stats['hit_rate']:.2%}")
        """
        self.cleanup()
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0
        
        return {
            'size': len(self._store),
            'max_size': self.max_size,
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': hit_rate,
            'eviction_policy': self.eviction_policy
        }
    
    def reset_stats(self):
        """Reset hit/miss statistics."""
        self._hits = 0
        self._misses = 0


# Global cache instance
_default_cache = Cache()


# Standalone API functions

def create(default_ttl=None, max_size=None, eviction_policy='lru'):
    """
    Create new cache instance.
    
    Args:
        default_ttl: Default TTL in seconds
        max_size: Maximum cache size
        eviction_policy: 'lru' or 'lfu'
    
    Returns:
        New Cache instance
    
    Example:
        my_cache = cache.create(default_ttl=3600, max_size=1000)
    """
    return Cache(default_ttl, max_size, eviction_policy)


def get(key, default=None):
    """
    Get from default cache.
    
    Args:
        key: Cache key
        default: Default value if not found
    
    Returns:
        Cached value or default
    """
    return _default_cache.get(key, default)


def set(key, value, ttl=None):
    """
    Set in default cache.
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: TTL in seconds
    """
    _default_cache.set(key, value, ttl)


def delete(key):
    """
    Delete from default cache.
    
    Args:
        key: Cache key
    """
    _default_cache.delete(key)


def clear():
    """Clear default cache."""
    _default_cache.clear()


def get_or_set(key, factory, ttl=None):
    """
    Get value or compute and cache it.
    
    Args:
        key: Cache key
        factory: Callable to compute value
        ttl: TTL in seconds
    
    Returns:
        Cached or computed value
    """
    return _default_cache.get_or_set(key, factory, ttl)


def increment(key, delta=1, default=0):
    """
    Increment numeric value in default cache.
    
    Args:
        key: Cache key
        delta: Amount to increment
        default: Initial value
    
    Returns:
        New value
    """
    return _default_cache.increment(key, delta, default)


def decrement(key, delta=1, default=0):
    """
    Decrement numeric value in default cache.
    
    Args:
        key: Cache key
        delta: Amount to decrement
        default: Initial value
    
    Returns:
        New value
    """
    return _default_cache.decrement(key, delta, default)


def get_many(keys):
    """
    Get multiple values from default cache.
    
    Args:
        keys: List of cache keys
    
    Returns:
        Dict of key-value pairs
    """
    return _default_cache.get_many(keys)


def set_many(items, ttl=None):
    """
    Set multiple values in default cache.
    
    Args:
        items: Dict of key-value pairs
        ttl: TTL in seconds
    """
    _default_cache.set_many(items, ttl)


def delete_many(keys):
    """
    Delete multiple keys from default cache.
    
    Args:
        keys: List of cache keys
    
    Returns:
        Number of keys deleted
    """
    return _default_cache.delete_many(keys)


def delete_pattern(pattern):
    """
    Delete keys matching pattern from default cache.
    
    Args:
        pattern: String pattern with * wildcard
    
    Returns:
        Number of keys deleted
    """
    return _default_cache.delete_pattern(pattern)


def keys(pattern=None):
    """
    Get all cache keys from default cache.
    
    Args:
        pattern: Optional pattern to filter
    
    Returns:
        List of cache keys
    """
    return _default_cache.keys(pattern)


def exists(key):
    """
    Check if key exists in default cache.
    
    Args:
        key: Cache key
    
    Returns:
        True if key exists
    """
    return _default_cache.exists(key)


def has(key):
    """
    Check if key exists (alias for exists).
    
    Args:
        key: Cache key
    
    Returns:
        True if key exists
    """
    return _default_cache.has(key)


def size():
    """
    Get default cache size.
    
    Returns:
        Number of cached items
    """
    return _default_cache.size()


def ttl(key):
    """
    Get remaining TTL for key in default cache.
    
    Args:
        key: Cache key
    
    Returns:
        Remaining seconds or None
    """
    return _default_cache.ttl(key)


def stats():
    """
    Get default cache statistics.
    
    Returns:
        Dict with cache stats
    """
    return _default_cache.stats()


def reset_stats():
    """Reset default cache statistics."""
    _default_cache.reset_stats()


def cleanup():
    """Remove expired entries from default cache."""
    return _default_cache.cleanup()


def memoize(ttl=None):
    """
    Decorator to memoize function results.
    
    Args:
        ttl: Cache TTL in seconds
    
    Returns:
        Decorator function
    
    Example:
        @cache.memoize(ttl=60)
        def expensive_calculation(x):
            return x ** 2
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Create cache key from function name and args
            key = f"{func.__name__}:{args}:{kwargs}"
            result = get(key)
            if result is None:
                result = func(*args, **kwargs)
                set(key, result, ttl=ttl)
            return result
        return wrapper
    return decorator


def touch(key, ttl=None):
    """
    Update TTL for existing key without changing value.
    
    Args:
        key: Cache key
        ttl: New TTL (None = default TTL)
    
    Returns:
        True if key exists
    
    Example:
        cache.touch("session:123", ttl=3600)
    """
    value = get(key)
    if value is not None:
        set(key, value, ttl=ttl)
        return True
    return False


__all__ = [
    'Cache',
    'CacheEntry',
    'create',
    'get',
    'set',
    'delete',
    'clear',
    'get_or_set',
    'increment',
    'decrement',
    'get_many',
    'set_many',
    'delete_many',
    'delete_pattern',
    'keys',
    'exists',
    'has',
    'size',
    'ttl',
    'stats',
    'reset_stats',
    'cleanup',
    'memoize',
    'touch'
]
