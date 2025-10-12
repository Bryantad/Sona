"""Timing helpers for quick measurements."""
from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Callable, Iterator, TypeVar

T = TypeVar("T")


class Timer:
    def __init__(self) -> None:
        self.elapsed: float = 0.0
        self._start: float | None = None

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._start is not None:
            self.elapsed = time.perf_counter() - self._start
            self._start = None


@contextmanager
def measure() -> Iterator[dict[str, float]]:
    start = time.perf_counter()
    info: dict[str, float] = {"elapsed": 0.0}
    try:
        yield info
    finally:
        info["elapsed"] = time.perf_counter() - start


def time_call(func: Callable[..., T], *args, **kwargs) -> tuple[T, float]:
    start = time.perf_counter()
    result = func(*args, **kwargs)
    return result, time.perf_counter() - start


__all__ = ["Timer", "measure", "time_call"]
