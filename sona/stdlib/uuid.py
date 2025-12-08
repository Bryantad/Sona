"""
Sona Standard Library - UUID Module

Provides UUID generation and validation functions.
Supports both random (v4) and deterministic (v5) UUID generation.

Stability: stable
Version: 0.9.6
"""

from __future__ import annotations
import uuid as _uuid

__all__ = ['v4', 'v5', 'v1', 'is_valid', 'generate']

def v4():
    """Generate a random UUID (version 4)."""
    return str(_uuid.uuid4())

def v5(namespace, name):
    """Generate a deterministic UUID (version 5) from namespace and name."""
    if isinstance(namespace, str):
        namespace = _uuid.UUID(namespace)
    return str(_uuid.uuid5(namespace, name))

def v1():
    """Generate a time-based UUID (version 1)."""
    return str(_uuid.uuid1())

def is_valid(uuid_string):
    """Validate a UUID string."""
    try:
        _uuid.UUID(str(uuid_string))
        return True
    except (ValueError, AttributeError, TypeError):
        return False

def generate(prefix=None):
    """Generate a UUID with optional prefix (legacy function)."""
    value = v4()
    return f"{prefix}{value}" if prefix else value


def v3(namespace, name):
    """
    Generate a deterministic UUID (version 3) using MD5.
    
    Args:
        namespace: Namespace UUID or string
        name: Name string
    
    Returns:
        UUID string
    
    Example:
        id = uuid.v3(uuid.NAMESPACE_DNS, "example.com")
    """
    if isinstance(namespace, str):
        namespace = _uuid.UUID(namespace)
    return str(_uuid.uuid3(namespace, name))


def nil():
    """
    Return nil UUID (all zeros).
    
    Returns:
        "00000000-0000-0000-0000-000000000000"
    
    Example:
        empty = uuid.nil()
    """
    return "00000000-0000-0000-0000-000000000000"


def to_bytes(uuid_string):
    """
    Convert UUID string to bytes.
    
    Args:
        uuid_string: UUID string
    
    Returns:
        16-byte representation
    
    Example:
        b = uuid.to_bytes("550e8400-e29b-41d4-a716-446655440000")
    """
    return _uuid.UUID(uuid_string).bytes


def from_bytes(uuid_bytes):
    """
    Convert bytes to UUID string.
    
    Args:
        uuid_bytes: 16-byte UUID
    
    Returns:
        UUID string
    
    Example:
        s = uuid.from_bytes(b'\\x55\\x0e...')
    """
    return str(_uuid.UUID(bytes=uuid_bytes))


def short():
    """
    Generate short UUID (first 8 characters of v4).
    
    Returns:
        Short UUID string
    
    Example:
        short_id = uuid.short()  # "a1b2c3d4"
    """
    return v4()[:8]


NAMESPACE_DNS = str(_uuid.NAMESPACE_DNS)
NAMESPACE_URL = str(_uuid.NAMESPACE_URL)
NAMESPACE_OID = str(_uuid.NAMESPACE_OID)
NAMESPACE_X500 = str(_uuid.NAMESPACE_X500)


__all__ = [
    'v4', 'v5', 'v1', 'v3', 'is_valid', 'generate',
    'nil', 'to_bytes', 'from_bytes', 'short',
    'NAMESPACE_DNS', 'NAMESPACE_URL', 'NAMESPACE_OID', 'NAMESPACE_X500'
]
