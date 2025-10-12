"""Result/Error helpers for Sona stdlib scaffolding.

This module centralises error handling semantics for the Sona standard library.
It provides a lightweight `Result[T]` container, canonical error codes, helper
constructors, and a thread-local "last error" registry for bridge code that
cannot yet return structured results.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import local
from typing import Any, Dict, Generic, Optional, TypeVar, Union

T = TypeVar("T")


class ErrorCode(str, Enum):
    """Enumerates stdlib error codes with stable string values."""

    EINVAL = "EINVAL"
    ENOTFOUND = "ENOTFOUND"
    EIO = "EIO"
    ESEC = "ESEC"
    ETIMEOUT = "ETIMEOUT"
    ECONN = "ECONN"
    EUNSUPPORTED = "EUNSUPPORTED"


@dataclass(frozen=True)
class SonaError:
    """Structured error payload returned from stdlib operations."""

    code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    cause: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "code": self.code.value,
            "message": self.message,
        }
        if self.details is not None:
            data["details"] = self.details
        if self.cause is not None:
            data["cause"] = self.cause
        return data


class Result(Generic[T]):
    """Container representing either a success (`ok`) or failure (`err`)."""

    __slots__ = ("_value", "_error")

    def __init__(
        self,
        value: Optional[T] = None,
        error: Optional[SonaError] = None,
    ):
        if (value is None) == (error is None):
            raise ValueError(
                "Result must contain exactly one of value or error"
            )
        self._value = value
        self._error = error

    def is_ok(self) -> bool:
        return self._error is None

    def is_err(self) -> bool:
        return self._error is not None

    def value(self) -> T:
        if self._value is None:
            raise RuntimeError("Called value() on an err result")
        return self._value

    def error(self) -> SonaError:
        if self._error is None:
            raise RuntimeError("Called error() on an ok result")
        return self._error

    def unwrap(self) -> T:
        """Return the inner value or raise with the error message."""
        if self.is_ok():
            return self._value  # type: ignore[return-value]
        err = self.error()
        raise RuntimeError(
            f"Result.unwrap() failed: {err.code.value} {err.message}"
        )

    def unwrap_or(self, default: T) -> T:
        return self._value if self.is_ok() else default

    def expect(self, message: str) -> T:
        if self.is_ok():
            return self._value  # type: ignore[return-value]
        err = self.error()
        raise RuntimeError(f"{message}: {err.code.value} {err.message}")

    def map(self, func):
        if self.is_ok():
            return ok(func(self._value))  # type: ignore[arg-type]
        return self  # type: ignore[return-value]

    def bind(self, func):
        if self.is_ok():
            return func(self._value)  # type: ignore[arg-type]
        return self  # type: ignore[return-value]

    def __repr__(self) -> str:
        if self.is_ok():
            return f"Result.ok({self._value!r})"
        return f"Result.err({self._error!r})"


_state = local()


def _get_state() -> Dict[str, Any]:
    if not hasattr(_state, "data"):
        _state.data = {"last_error": None}
    return _state.data  # type: ignore[return-value]


def ok(value: T) -> Result[T]:
    """Create a successful result and clear the thread-local last error."""
    set_last_error(None)
    return Result(value=value)


def err(
    code: Union[ErrorCode, str],
    message: str,
    *,
    details: Optional[Dict[str, Any]] = None,
    cause: Optional[str] = None,
) -> Result[Any]:
    """Create a failed result, record it as the last error, and return it."""
    if isinstance(code, str):
        try:
            code = ErrorCode(code)
        except ValueError as exc:  # pragma: no cover - defensive branch
            raise ValueError(f"Unknown error code: {code}") from exc
    error = SonaError(code=code, message=message, details=details, cause=cause)
    set_last_error(error)
    return Result(error=error)


def last_error() -> Optional[SonaError]:
    """Return the most recent error recorded on this thread, if any."""
    return _get_state()["last_error"]


def set_last_error(error: Optional[SonaError]) -> None:
    """Store an error in the thread-local registry for legacy return paths."""
    _get_state()["last_error"] = error


def from_optional(
    value: Optional[T],
    code: Union[ErrorCode, str],
    message: str,
) -> Result[T]:
    """Promote an optional into a Result using a fallback error payload."""
    if value is None:
        return err(code, message)
    return ok(value)


def from_callable(func, *args, **kwargs) -> Result[Any]:
    """Execute a callable and capture exceptions as `EIO` errors."""
    try:
        return ok(func(*args, **kwargs))
    except Exception as exc:  # pragma: no cover - passthrough path
        return err(ErrorCode.EIO, str(exc), cause=exc.__class__.__name__)
