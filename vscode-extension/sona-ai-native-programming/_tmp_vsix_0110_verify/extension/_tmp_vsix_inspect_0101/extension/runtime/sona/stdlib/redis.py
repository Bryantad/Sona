"""
redis - Comprehensive Redis client for Sona stdlib

Provides complete Redis operations (mock implementation).
For production use, install redis-py package.

Features:
- Strings: get, set, incr, decr, mget, mset
- Lists: lpush, rpush, lpop, rpop, lrange, llen
- Sets: sadd, srem, smembers, sismember, scard
- Hashes: hset, hget, hdel, hgetall, hkeys, hvals
- Sorted Sets: zadd, zrem, zrange, zscore
- TTL: expire, ttl, persist
- Pub/Sub: publish, subscribe (mock)
- Pipeline: pipeline context
"""

import time
from collections import defaultdict


class RedisClient:
    """Mock Redis client (in-memory) with comprehensive Redis API."""
    
    def __init__(self, host='localhost', port=6379, db=0):
        """Initialize client."""
        self.host = host
        self.port = port
        self.db = db
        # Data structures
        self.data = {}  # Strings
        self.lists = {}  # Lists
        self.sets = {}  # Sets
        self.hashes = {}  # Hashes
        self.sorted_sets = {}  # Sorted sets
        # TTL tracking
        self.expiry = {}
        # Pub/Sub
        self.pubsub_channels = defaultdict(list)
    
    def set(self, key, value, ex=None):
        """Set string value."""
        self.data[key] = value
        return True
    
    def get(self, key):
        """Get string value."""
        return self.data.get(key)
    
    def delete(self, key):
        """Delete key."""
        self.data.pop(key, None)
        self.lists.pop(key, None)
        self.sets.pop(key, None)
        return True
    
    def exists(self, key):
        """Check if key exists."""
        return key in self.data or key in self.lists or key in self.sets
    
    def lpush(self, key, *values):
        """Push to list (left)."""
        if key not in self.lists:
            self.lists[key] = []
        for value in reversed(values):
            self.lists[key].insert(0, value)
        return len(self.lists[key])
    
    def rpush(self, key, *values):
        """Push to list (right)."""
        if key not in self.lists:
            self.lists[key] = []
        self.lists[key].extend(values)
        return len(self.lists[key])
    
    def lpop(self, key):
        """Pop from list (left)."""
        if key in self.lists and self.lists[key]:
            return self.lists[key].pop(0)
        return None
    
    def rpop(self, key):
        """Pop from list (right)."""
        if key in self.lists and self.lists[key]:
            return self.lists[key].pop()
        return None
    
    def lrange(self, key, start, stop):
        """Get list range."""
        if key in self.lists:
            return self.lists[key][start:stop+1]
        return []
    
    def sadd(self, key, *members):
        """Add to set."""
        if key not in self.sets:
            self.sets[key] = set()
        self.sets[key].update(members)
        return len(members)
    
    def smembers(self, key):
        """Get all set members."""
        return list(self.sets.get(key, set()))
    
    def srem(self, key, *members):
        """Remove from set."""
        if key in self.sets:
            self.sets[key].difference_update(members)
        return True
    
    def incr(self, key, amount=1):
        """Increment value."""
        current = int(self.data.get(key, 0))
        self.data[key] = str(current + amount)
        return current + amount
    
    def decr(self, key, amount=1):
        """Decrement value."""
        return self.incr(key, -amount)
    
    def mget(self, *keys):
        """Get multiple values."""
        return [self.data.get(key) for key in keys]
    
    def mset(self, mapping):
        """Set multiple key-value pairs."""
        self.data.update(mapping)
        return True
    
    # List operations (additional)
    def llen(self, key):
        """Get list length."""
        return len(self.lists.get(key, []))
    
    def lindex(self, key, index):
        """Get list element by index."""
        if key in self.lists:
            try:
                return self.lists[key][index]
            except IndexError:
                return None
        return None
    
    def lrem(self, key, count, value):
        """Remove elements from list."""
        if key not in self.lists:
            return 0
        removed = 0
        if count == 0:
            # Remove all occurrences
            self.lists[key] = [v for v in self.lists[key] if v != value]
            removed = len(self.lists[key])
        elif count > 0:
            # Remove from head
            for _ in range(count):
                try:
                    self.lists[key].remove(value)
                    removed += 1
                except ValueError:
                    break
        else:
            # Remove from tail
            for _ in range(abs(count)):
                try:
                    idx = len(self.lists[key]) - 1 - self.lists[key][::-1].index(value)
                    self.lists[key].pop(idx)
                    removed += 1
                except ValueError:
                    break
        return removed
    
    # Set operations (additional)
    def sismember(self, key, member):
        """Check if member is in set."""
        return member in self.sets.get(key, set())
    
    def scard(self, key):
        """Get set cardinality (size)."""
        return len(self.sets.get(key, set()))
    
    def sinter(self, *keys):
        """Get intersection of sets."""
        if not keys:
            return set()
        result = self.sets.get(keys[0], set()).copy()
        for key in keys[1:]:
            result &= self.sets.get(key, set())
        return list(result)
    
    def sunion(self, *keys):
        """Get union of sets."""
        result = set()
        for key in keys:
            result |= self.sets.get(key, set())
        return list(result)
    
    def sdiff(self, *keys):
        """Get difference of sets."""
        if not keys:
            return set()
        result = self.sets.get(keys[0], set()).copy()
        for key in keys[1:]:
            result -= self.sets.get(key, set())
        return list(result)
    
    # Hash operations
    def hset(self, name, key, value):
        """Set hash field."""
        if name not in self.hashes:
            self.hashes[name] = {}
        self.hashes[name][key] = value
        return 1
    
    def hget(self, name, key):
        """Get hash field."""
        return self.hashes.get(name, {}).get(key)
    
    def hdel(self, name, *keys):
        """Delete hash fields."""
        if name not in self.hashes:
            return 0
        count = 0
        for key in keys:
            if key in self.hashes[name]:
                del self.hashes[name][key]
                count += 1
        return count
    
    def hgetall(self, name):
        """Get all hash fields and values."""
        return self.hashes.get(name, {}).copy()
    
    def hkeys(self, name):
        """Get all hash field names."""
        return list(self.hashes.get(name, {}).keys())
    
    def hvals(self, name):
        """Get all hash values."""
        return list(self.hashes.get(name, {}).values())
    
    def hexists(self, name, key):
        """Check if hash field exists."""
        return key in self.hashes.get(name, {})
    
    def hlen(self, name):
        """Get number of hash fields."""
        return len(self.hashes.get(name, {}))
    
    def hincrby(self, name, key, amount=1):
        """Increment hash field."""
        if name not in self.hashes:
            self.hashes[name] = {}
        current = int(self.hashes[name].get(key, 0))
        self.hashes[name][key] = str(current + amount)
        return current + amount
    
    # Sorted set operations
    def zadd(self, name, mapping):
        """Add to sorted set (mapping of member: score)."""
        if name not in self.sorted_sets:
            self.sorted_sets[name] = {}
        self.sorted_sets[name].update(mapping)
        return len(mapping)
    
    def zrem(self, name, *members):
        """Remove from sorted set."""
        if name not in self.sorted_sets:
            return 0
        count = 0
        for member in members:
            if member in self.sorted_sets[name]:
                del self.sorted_sets[name][member]
                count += 1
        return count
    
    def zscore(self, name, member):
        """Get score of sorted set member."""
        return self.sorted_sets.get(name, {}).get(member)
    
    def zrange(self, name, start, stop, withscores=False):
        """Get sorted set range."""
        if name not in self.sorted_sets:
            return []
        items = sorted(self.sorted_sets[name].items(), key=lambda x: x[1])
        items = items[start:stop+1 if stop >= 0 else None]
        if withscores:
            return items
        return [item[0] for item in items]
    
    def zcard(self, name):
        """Get sorted set cardinality."""
        return len(self.sorted_sets.get(name, {}))
    
    # TTL operations
    def expire(self, key, seconds):
        """Set key expiration."""
        self.expiry[key] = time.time() + seconds
        return True
    
    def ttl(self, key):
        """Get key TTL."""
        if key not in self.expiry:
            return -1
        remaining = self.expiry[key] - time.time()
        if remaining <= 0:
            self._expire_key(key)
            return -2
        return int(remaining)
    
    def persist(self, key):
        """Remove key expiration."""
        if key in self.expiry:
            del self.expiry[key]
            return True
        return False
    
    def _expire_key(self, key):
        """Remove expired key from all data structures."""
        self.data.pop(key, None)
        self.lists.pop(key, None)
        self.sets.pop(key, None)
        self.hashes.pop(key, None)
        self.sorted_sets.pop(key, None)
        self.expiry.pop(key, None)
    
    def _check_expiry(self, key):
        """Check and handle key expiration."""
        if key in self.expiry and time.time() >= self.expiry[key]:
            self._expire_key(key)
            return True
        return False
    
    # Pub/Sub operations (mock)
    def publish(self, channel, message):
        """Publish message to channel (mock)."""
        subscribers = len(self.pubsub_channels.get(channel, []))
        return subscribers
    
    def subscribe(self, *channels):
        """Subscribe to channels (mock)."""
        for channel in channels:
            if channel not in self.pubsub_channels:
                self.pubsub_channels[channel] = []
        return True
    
    # Pipeline support
    def pipeline(self):
        """Create pipeline (returns self for mock)."""
        return _Pipeline(self)
    
    # Key operations
    def keys(self, pattern='*'):
        """Get all keys matching pattern."""
        import re
        if pattern == '*':
            all_keys = set()
            all_keys.update(self.data.keys())
            all_keys.update(self.lists.keys())
            all_keys.update(self.sets.keys())
            all_keys.update(self.hashes.keys())
            all_keys.update(self.sorted_sets.keys())
            return list(all_keys)
        
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        regex = re.compile(f"^{regex_pattern}$")
        
        all_keys = set()
        all_keys.update(k for k in self.data.keys() if regex.match(k))
        all_keys.update(k for k in self.lists.keys() if regex.match(k))
        all_keys.update(k for k in self.sets.keys() if regex.match(k))
        all_keys.update(k for k in self.hashes.keys() if regex.match(k))
        all_keys.update(k for k in self.sorted_sets.keys() if regex.match(k))
        return list(all_keys)
    
    def flushdb(self):
        """Clear database."""
        self.data.clear()
        self.lists.clear()
        self.sets.clear()
        self.hashes.clear()
        self.sorted_sets.clear()
        self.expiry.clear()
        return True


class _Pipeline:
    """Pipeline for batching Redis commands."""
    
    def __init__(self, client):
        self.client = client
        self.commands = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        return self.execute()
    
    def execute(self):
        """Execute all pipelined commands."""
        results = []
        for cmd, args, kwargs in self.commands:
            method = getattr(self.client, cmd)
            results.append(method(*args, **kwargs))
        self.commands.clear()
        return results
    
    def __getattr__(self, name):
        """Capture command calls."""
        def wrapper(*args, **kwargs):
            self.commands.append((name, args, kwargs))
            return self
        return wrapper


# Global client instance
_default_client = None


def connect(host='localhost', port=6379, db=0):
    """
    Connect to Redis server (creates mock client).
    
    Args:
        host: Redis host
        port: Redis port
        db: Database number
    
    Returns:
        RedisClient object
    
    Example:
        client = redis.connect()
        client.set("key", "value")
        value = client.get("key")
    """
    global _default_client
    _default_client = RedisClient(host, port, db)
    return _default_client


def get_client():
    """Get or create default Redis client."""
    global _default_client
    if _default_client is None:
        _default_client = RedisClient()
    return _default_client


# Standalone API functions (use default client)

# String operations
def get(key):
    """Get string value."""
    return get_client().get(key)


def set(key, value, ex=None):
    """Set string value."""
    return get_client().set(key, value, ex)


def incr(key, amount=1):
    """Increment value."""
    return get_client().incr(key, amount)


def decr(key, amount=1):
    """Decrement value."""
    return get_client().decr(key, amount)


def mget(*keys):
    """Get multiple values."""
    return get_client().mget(*keys)


def mset(mapping):
    """Set multiple values."""
    return get_client().mset(mapping)


# Key operations
def delete(key):
    """Delete key."""
    return get_client().delete(key)


def exists(key):
    """Check if key exists."""
    return get_client().exists(key)


def keys(pattern='*'):
    """Get all keys matching pattern."""
    return get_client().keys(pattern)


# List operations
def lpush(key, *values):
    """Push to list (left)."""
    return get_client().lpush(key, *values)


def rpush(key, *values):
    """Push to list (right)."""
    return get_client().rpush(key, *values)


def lpop(key):
    """Pop from list (left)."""
    return get_client().lpop(key)


def rpop(key):
    """Pop from list (right)."""
    return get_client().rpop(key)


def lrange(key, start, stop):
    """Get list range."""
    return get_client().lrange(key, start, stop)


def llen(key):
    """Get list length."""
    return get_client().llen(key)


def lindex(key, index):
    """Get list element by index."""
    return get_client().lindex(key, index)


# Set operations
def sadd(key, *members):
    """Add to set."""
    return get_client().sadd(key, *members)


def srem(key, *members):
    """Remove from set."""
    return get_client().srem(key, *members)


def smembers(key):
    """Get all set members."""
    return get_client().smembers(key)


def sismember(key, member):
    """Check if member is in set."""
    return get_client().sismember(key, member)


def scard(key):
    """Get set size."""
    return get_client().scard(key)


def sinter(*keys):
    """Get intersection of sets."""
    return get_client().sinter(*keys)


def sunion(*keys):
    """Get union of sets."""
    return get_client().sunion(*keys)


def sdiff(*keys):
    """Get difference of sets."""
    return get_client().sdiff(*keys)


# Hash operations
def hset(name, key, value):
    """Set hash field."""
    return get_client().hset(name, key, value)


def hget(name, key):
    """Get hash field."""
    return get_client().hget(name, key)


def hdel(name, *keys):
    """Delete hash fields."""
    return get_client().hdel(name, *keys)


def hgetall(name):
    """Get all hash fields."""
    return get_client().hgetall(name)


def hkeys(name):
    """Get all hash field names."""
    return get_client().hkeys(name)


def hvals(name):
    """Get all hash values."""
    return get_client().hvals(name)


def hexists(name, key):
    """Check if hash field exists."""
    return get_client().hexists(name, key)


def hlen(name):
    """Get number of hash fields."""
    return get_client().hlen(name)


def hincrby(name, key, amount=1):
    """Increment hash field."""
    return get_client().hincrby(name, key, amount)


# Sorted set operations
def zadd(name, mapping):
    """Add to sorted set."""
    return get_client().zadd(name, mapping)


def zrem(name, *members):
    """Remove from sorted set."""
    return get_client().zrem(name, *members)


def zscore(name, member):
    """Get score of member."""
    return get_client().zscore(name, member)


def zrange(name, start, stop, withscores=False):
    """Get sorted set range."""
    return get_client().zrange(name, start, stop, withscores)


def zcard(name):
    """Get sorted set size."""
    return get_client().zcard(name)


# TTL operations
def expire(key, seconds):
    """Set key expiration."""
    return get_client().expire(key, seconds)


def ttl(key):
    """Get key TTL."""
    return get_client().ttl(key)


def persist(key):
    """Remove key expiration."""
    return get_client().persist(key)


# Pub/Sub operations
def publish(channel, message):
    """Publish message to channel."""
    return get_client().publish(channel, message)


def subscribe(*channels):
    """Subscribe to channels."""
    return get_client().subscribe(*channels)


# Pipeline
def pipeline():
    """Create pipeline."""
    return get_client().pipeline()


# Database operations
def flushdb():
    """Clear database."""
    return get_client().flushdb()


__all__ = [
    'RedisClient',
    'connect',
    'get_client',
    'get',
    'set',
    'incr',
    'decr',
    'mget',
    'mset',
    'delete',
    'exists',
    'keys',
    'lpush',
    'rpush',
    'lpop',
    'rpop',
    'lrange',
    'llen',
    'lindex',
    'sadd',
    'srem',
    'smembers',
    'sismember',
    'scard',
    'sinter',
    'sunion',
    'sdiff',
    'hset',
    'hget',
    'hdel',
    'hgetall',
    'hkeys',
    'hvals',
    'hexists',
    'hlen',
    'hincrby',
    'zadd',
    'zrem',
    'zscore',
    'zrange',
    'zcard',
    'expire',
    'ttl',
    'persist',
    'publish',
    'subscribe',
    'pipeline',
    'flushdb',
]
