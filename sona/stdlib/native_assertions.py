"""Collision-safe native backing for the public Sona `assert` module."""

from __future__ import annotations

from typing import Any


class SonaAssertionFailure(AssertionError):
    """Structured assertion failure used by Sona assertion helpers."""


def _message(default: str, message: Any = "") -> str:
    text = str(message or "")
    return text if text else default


def assert_equal(actual: Any, expected: Any, message: Any = "") -> bool:
    if actual != expected:
        raise SonaAssertionFailure(_message(f"Expected {expected!r}, got {actual!r}", message))
    return True


def assert_not_equal(actual: Any, expected: Any, message: Any = "") -> bool:
    if actual == expected:
        raise SonaAssertionFailure(_message(f"Expected value different from {expected!r}", message))
    return True


def assert_true(value: Any, message: Any = "") -> bool:
    if not value:
        raise SonaAssertionFailure(_message(f"Expected true value, got {value!r}", message))
    return True


def assert_false(value: Any, message: Any = "") -> bool:
    if value:
        raise SonaAssertionFailure(_message(f"Expected false value, got {value!r}", message))
    return True


true = assert_true
false = assert_false


def assert_contains(container: Any, value: Any, message: Any = "") -> bool:
    if value not in container:
        raise SonaAssertionFailure(_message(f"Expected {value!r} in {container!r}", message))
    return True


def assert_fail(message: Any = "Assertion failed") -> None:
    raise SonaAssertionFailure(str(message or "Assertion failed"))


def _call(candidate: Any) -> Any:
    if hasattr(candidate, "call"):
        return candidate.call([], {})
    return candidate()


def assert_raises(callable_or_wrapper: Any, expected_error: Any = Exception, message: Any = "") -> bool:
    expected_name = str(expected_error)
    try:
        if isinstance(expected_error, type):
            expected_name = expected_error.__name__
        _call(callable_or_wrapper)
    except Exception as exc:  # noqa: BLE001 - assertion helper compares exception type
        if expected_error in (Exception, "Exception") or type(exc).__name__ == expected_name:
            return True
        raise SonaAssertionFailure(
            _message(f"Expected {expected_name}, got {type(exc).__name__}", message)
        ) from exc
    raise SonaAssertionFailure(_message(f"Expected {expected_name} to be raised", message))


__all__ = [
    "SonaAssertionFailure",
    "assert_equal",
    "assert_not_equal",
    "assert_true",
    "assert_false",
    "true",
    "false",
    "assert_contains",
    "assert_raises",
    "assert_fail",
]
