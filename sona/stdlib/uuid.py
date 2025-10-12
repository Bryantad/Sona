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
