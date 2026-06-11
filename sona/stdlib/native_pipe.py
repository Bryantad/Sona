"""Native backing for simple functional pipeline helpers."""

from __future__ import annotations

from functools import reduce as _py_reduce
from typing import Any


def _call(fn: Any, *args: Any) -> Any:
    if hasattr(fn, "call"):
        return fn.call(list(args), {})
    return fn(*args)


def pipe_map(values: Any, callable_obj: Any) -> list[Any]:
    return [_call(callable_obj, value) for value in list(values or [])]


def pipe_filter(values: Any, callable_obj: Any) -> list[Any]:
    return [value for value in list(values or []) if _call(callable_obj, value)]


def pipe_reduce(values: Any, callable_obj: Any, initial: Any = None) -> Any:
    items = list(values or [])
    if initial is None and items:
        return _py_reduce(lambda acc, value: _call(callable_obj, acc, value), items)
    return _py_reduce(lambda acc, value: _call(callable_obj, acc, value), items, initial)


def pipe_each(values: Any, callable_obj: Any) -> list[Any]:
    for value in list(values or []):
        _call(callable_obj, value)
    return list(values or [])


def pipe_compose(functions: Any):
    funcs = list(functions or [])

    def composed(value):
        result = value
        for fn in reversed(funcs):
            result = _call(fn, result)
        return result

    return composed


def pipe_take(values: Any, count: Any) -> list[Any]:
    return list(values or [])[: max(0, int(count))]


def pipe_drop(values: Any, count: Any) -> list[Any]:
    return list(values or [])[max(0, int(count)) :]


def pipe_unique(values: Any) -> list[Any]:
    result = []
    for value in list(values or []):
        if value not in result:
            result.append(value)
    return result


__all__ = [
    "pipe_map",
    "pipe_filter",
    "pipe_reduce",
    "pipe_each",
    "pipe_compose",
    "pipe_take",
    "pipe_drop",
    "pipe_unique",
]
