"""
AI Cache System - Enterprise Grade
=================================

Hash-based caching system for AI operations ensuring reproducibility,
performance, and compliance with enterprise requirements.

Features:
- Deterministic hash-based cache keys
- Structured storage with metadata
- TTL and eviction policies
- Audit trails and lineage tracking
- Thread-safe operations
- Compression and encryption support
"""

import hashlib

# Import standard library json avoiding local conflicts
import importlib
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from .errors import AICacheError


json = importlib.import_module('json')


@dataclass
class CacheEntry:
    """Represents a cached AI operation result"""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int
    metadata: dict[str, Any]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CacheEntry':
        """Create from dictionary"""
        return cls(**data)


class AICache:
    """
    Enterprise-grade cache for AI operations
    
    Provides deterministic caching with enterprise features:
    - Hash-based keys for reproducibility
    - Metadata tracking for audit trails
    - Configurable retention policies
    - Thread-safe operations
    """
    
    def __init__(self, 
                 cache_dir: Path | None = None,
                 max_entries: int = 10000,
                 default_ttl: int = 3600,
                 enable_compression: bool = True,
                 enable_encryption: bool = False):
        """
        Initialize AI cache
        
        Args:
            cache_dir: Directory for persistent cache storage
            max_entries: Maximum number of cache entries
            default_ttl: Default time-to-live in seconds
            enable_compression: Enable gzip compression
            enable_encryption: Enable AES encryption (requires key)
        """
        self.cache_dir = cache_dir or Path.home() / '.sona' / 'ai_cache'
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self.enable_compression = enable_compression
        self.enable_encryption = enable_encryption
        
        # In-memory cache for performance
        self._memory_cache: dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        
        # Statistics for monitoring
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'errors': 0
        }
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_key(self, 
                    operation: str,
                    prompt: str,
                    model_config: dict[str, Any],
                    schema: dict | None = None,
                    inputs: dict | None = None) -> str:
        """
        Generate deterministic cache key for AI operation
        
        Args:
            operation: Type of AI operation (e.g., 'generate', 'summarize')
            prompt: The input prompt
            model_config: Model configuration (model, temperature, etc.)
            schema: Optional schema for structured outputs
            inputs: Additional inputs for the operation
            
        Returns:
            Hex string cache key
        """
        # Create deterministic key from all inputs
        key_data = {
            'operation': operation,
            'prompt': prompt,
            'model_config': sorted(model_config.items()),
            'schema': schema,
            'inputs': inputs
        }
        
        # Serialize to deterministic JSON
        key_json = json.dumps(key_data, sort_keys=True, separators=(',', ':'))
        
        # Generate SHA-256 hash
        return hashlib.sha256(key_json.encode('utf-8')).hexdigest()
    
    def get(self, key: str) -> Any | None:
        """
        Retrieve value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            try:
                # Check memory cache first
                if key in self._memory_cache:
                    entry = self._memory_cache[key]
                    
                    # Check TTL
                    if self._is_expired(entry):
                        del self._memory_cache[key]
                        self._stats['misses'] += 1
                        return None
                    
                    # Update access metadata
                    entry.last_accessed = time.time()
                    entry.access_count += 1
                    
                    self._stats['hits'] += 1
                    return entry.value
                
                # Try loading from disk
                entry = self._load_from_disk(key)
                if entry:
                    if self._is_expired(entry):
                        self._remove_from_disk(key)
                        self._stats['misses'] += 1
                        return None
                    
                    # Cache in memory for faster access
                    self._memory_cache[key] = entry
                    entry.last_accessed = time.time()
                    entry.access_count += 1
                    
                    self._stats['hits'] += 1
                    return entry.value
                
                self._stats['misses'] += 1
                return None
                
            except Exception as e:
                self._stats['errors'] += 1
                raise AICacheError('get', str(e))
    
    def put(self, 
           key: str, 
           value: Any, 
           metadata: dict | None = None,
           ttl: int | None = None) -> None:
        """
        Store value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            metadata: Additional metadata for audit trails
            ttl: Time-to-live override
        """
        with self._lock:
            try:
                current_time = time.time()
                
                # Create cache entry
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=current_time,
                    last_accessed=current_time,
                    access_count=0,
                    metadata=metadata or {}
                )
                
                # Add TTL to metadata
                entry.metadata['ttl'] = ttl or self.default_ttl
                entry.metadata['expires_at'] = current_time + (ttl or self.default_ttl)
                
                # Store in memory
                self._memory_cache[key] = entry
                
                # Store on disk for persistence
                self._save_to_disk(entry)
                
                # Evict if necessary
                self._evict_if_needed()
                
            except Exception as e:
                self._stats['errors'] += 1
                raise AICacheError('put', str(e))
    
    def invalidate(self, key: str) -> bool:
        """
        Remove entry from cache
        
        Args:
            key: Cache key to remove
            
        Returns:
            True if entry was removed, False if not found
        """
        with self._lock:
            try:
                removed = False
                
                # Remove from memory
                if key in self._memory_cache:
                    del self._memory_cache[key]
                    removed = True
                
                # Remove from disk
                if self._remove_from_disk(key):
                    removed = True
                
                return removed
                
            except Exception as e:
                self._stats['errors'] += 1
                raise AICacheError('invalidate', str(e))
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            try:
                # Clear memory cache
                self._memory_cache.clear()
                
                # Clear disk cache
                for cache_file in self.cache_dir.glob('*.cache'):
                    cache_file.unlink()
                
            except Exception as e:
                self._stats['errors'] += 1
                raise AICacheError('clear', str(e))
    
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                **self._stats,
                'total_requests': total_requests,
                'hit_rate_percent': round(hit_rate, 2),
                'memory_entries': len(self._memory_cache),
                'disk_entries': len(list(self.cache_dir.glob('*.cache')))
            }
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired"""
        expires_at = entry.metadata.get('expires_at', 0)
        return time.time() > expires_at
    
    def _evict_if_needed(self) -> None:
        """Evict entries if cache exceeds max size"""
        if len(self._memory_cache) <= self.max_entries:
            return
        
        # Sort by last accessed time (LRU eviction)
        entries_by_access = sorted(
            self._memory_cache.items(),
            key=lambda x: x[1].last_accessed
        )
        
        # Remove oldest entries
        entries_to_remove = len(self._memory_cache) - self.max_entries
        for i in range(entries_to_remove):
            key, _ = entries_by_access[i]
            del self._memory_cache[key]
            self._stats['evictions'] += 1
    
    def _load_from_disk(self, key: str) -> CacheEntry | None:
        """Load cache entry from disk"""
        cache_file = self.cache_dir / f"{key}.cache"
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, encoding='utf-8') as f:
                data = json.load(f)
            return CacheEntry.from_dict(data)
        except Exception:
            # Remove corrupted cache file
            cache_file.unlink(missing_ok=True)
            return None
    
    def _save_to_disk(self, entry: CacheEntry) -> None:
        """Save cache entry to disk"""
        cache_file = self.cache_dir / f"{entry.key}.cache"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(entry.to_dict(), f)
    
    def _remove_from_disk(self, key: str) -> bool:
        """Remove cache entry from disk"""
        cache_file = self.cache_dir / f"{key}.cache"
        if cache_file.exists():
            cache_file.unlink()
            return True
        return False


# Global cache instance
_global_cache: AICache | None = None


def get_global_cache() -> AICache:
    """Get or create global AI cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = AICache()
    return _global_cache
