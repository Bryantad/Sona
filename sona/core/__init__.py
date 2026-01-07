"""
Sona core helpers.

Legacy class system experiments moved to sona._attic.core.
"""

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
