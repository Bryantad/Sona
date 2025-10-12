"""Circuit breaker and retry utilities (feature gated).

Implements a simple error-rate based circuit breaker with half-open probing
and exponential backoff with jitter.
"""
from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass

from ..flags import get_flags


@dataclass
class BreakerState:
    failures: int = 0
    successes: int = 0
    opened_at: float = 0.0
    state: str = "closed"  # closed | open | half_open

    def error_rate(self) -> float:
        total = self.failures + self.successes
        if total == 0:
            return 0.0
        return self.failures / max(total, 1)

    def record_success(self) -> None:
        self.successes += 1
        if self.state == "half_open":
            # Close breaker on first success
            self.reset()

    def record_failure(self) -> None:
        self.failures += 1

    def open(self) -> None:
        self.state = "open"
        self.opened_at = time.time()

    def half_open(self) -> None:
        self.state = "half_open"

    def reset(self) -> None:
        self.failures = 0
        self.successes = 0
        self.state = "closed"
        self.opened_at = 0.0


class CircuitBreaker:
    def __init__(
        self,
        max_error_rate: float,
        min_calls: int = 10,
        open_cooldown: float = 5.0,
        half_open_max_calls: int = 1,
        time_func: Callable[[], float] | None = None,
    ):
        self.max_error_rate = max_error_rate
        self.min_calls = min_calls
        self.open_cooldown = open_cooldown
        self.half_open_max_calls = half_open_max_calls
        self.state = BreakerState()
        self._half_open_calls = 0
        self.time = time_func or time.time

    def allow(self) -> bool:
        if self.state.state == "closed":
            return True
        if self.state.state == "open":
            if self.time() - self.state.opened_at >= self.open_cooldown:
                self.state.half_open()
                self._half_open_calls = 0
                return True
            return False
        # half_open
        if self._half_open_calls < self.half_open_max_calls:
            self._half_open_calls += 1
            return True
        return False

    def record(self, success: bool) -> None:
        if success:
            self.state.record_success()
        else:
            self.state.record_failure()
        # Evaluate transition
        calls = self.state.failures + self.state.successes
        if calls >= self.min_calls and self.state.state == "closed":
            if self.state.error_rate() >= self.max_error_rate:
                self.state.open()
        elif self.state.state == "half_open" and not success:
            # Failure while half-open -> reopen
            self.state.open()

    def snapshot(self) -> dict[str, float | str | int]:
        return {
            "state": self.state.state,
            "failures": self.state.failures,
            "successes": self.state.successes,
            "error_rate": round(self.state.error_rate(), 4),
        }


def backoff(
    base: float, attempt: int, jitter: float = 0.2, cap: float = 30.0
) -> float:
    raw = base * (2 ** attempt)
    raw = min(raw, cap)
    # Jitter range ± jitter * raw
    delta = raw * jitter
    return random.uniform(raw - delta, raw + delta)


_global_breaker: CircuitBreaker | None = None


def get_breaker() -> CircuitBreaker | None:
    flags = get_flags()
    if not flags.enable_breaker:
        return None
    global _global_breaker
    if _global_breaker is None:
        _global_breaker = CircuitBreaker(flags.breaker_error_rate or 0.3)
    return _global_breaker
