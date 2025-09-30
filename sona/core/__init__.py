"""
Sona Language Core Features
 = (
    ========================= This module provides the core features for the Sona language including:
)
- Object-oriented programming system
- Advanced data structures
- Type system enhancements
- Memory management utilities
"""

from .classes import (
    STANDARD_METHODS,
    BoundClassMethod,
    BoundMethod,
    ClassBuilder,
    InheritanceManager,
    PropertyDescriptor,
    SonaClass,
    SonaObject,
    create_class,
    super_call,
)
from .result import (
    ErrorCode,
    Result,
    SonaError,
    err,
    from_callable,
    from_optional,
    last_error,
    ok,
    set_last_error,
)


__all__ = [
    "SonaClass",
    "SonaObject",
    "BoundMethod",
    "BoundClassMethod",
    "PropertyDescriptor",
    "ClassBuilder",
    "InheritanceManager",
    "create_class",
    "super_call",
    "STANDARD_METHODS",
    "Result",
    "SonaError",
    "ErrorCode",
    "ok",
    "err",
    "last_error",
    "set_last_error",
    "from_optional",
    "from_callable",
]
