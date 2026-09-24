"""Time-aware health and heartbeat contracts, separate from authorization."""

from __future__ import annotations

import math
import re
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from .contracts import HealthState

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SAFE_DIAGNOSTIC = re.compile(r"^[A-Z][A-Z0-9_-]{0,63}$")


def _finite_positive(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be finite and positive")
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{field_name} must be finite and positive") from exc
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{field_name} must be finite and positive")
    return result


@dataclass(frozen=True, slots=True)
class HealthPolicy:
    degraded_after_seconds: float = 10.0
    unhealthy_after_seconds: float = 30.0

    def __post_init__(self) -> None:
        degraded_after = _finite_positive(
            self.degraded_after_seconds, "degraded_after_seconds"
        )
        unhealthy_after = _finite_positive(
            self.unhealthy_after_seconds, "unhealthy_after_seconds"
        )
        if degraded_after > 30 * 24 * 60 * 60 or unhealthy_after > 30 * 24 * 60 * 60:
            raise ValueError("health thresholds cannot exceed 30 days")
        if unhealthy_after <= degraded_after:
            raise ValueError("unhealthy threshold must be greater than degraded threshold")


@dataclass(frozen=True, slots=True)
class HealthSnapshot:
    subject_id: str
    state: HealthState
    sequence: int
    heartbeat_count: int
    last_observed_at_utc: str | None
    age_seconds: float | None
    diagnostic_code: str | None


@dataclass(slots=True)
class _HealthRecord:
    policy: HealthPolicy
    state: HealthState = HealthState.UNKNOWN
    sequence: int = 0
    heartbeat_count: int = 0
    observed_monotonic: float | None = None
    observed_at_utc: str | None = None
    diagnostic_code: str | None = None


class HealthMonitor:
    """Thread-safe health registry whose freshness is evaluated on snapshot."""

    def __init__(
        self,
        *,
        monotonic_clock: Callable[[], float] = time.monotonic,
        utc_clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not callable(monotonic_clock):
            raise TypeError("monotonic_clock must be callable")
        if utc_clock is not None and not callable(utc_clock):
            raise TypeError("utc_clock must be callable")
        self._monotonic_clock = monotonic_clock
        self._utc_clock = utc_clock or (lambda: datetime.now(UTC))
        self._lock = threading.RLock()
        self._records: dict[str, _HealthRecord] = {}

    def register(self, subject_id: str, policy: HealthPolicy = HealthPolicy()) -> None:
        if not isinstance(subject_id, str) or not _SAFE_ID.fullmatch(subject_id):
            raise ValueError("subject_id must be a safe identifier")
        if not isinstance(policy, HealthPolicy):
            raise TypeError("policy must be a HealthPolicy")
        with self._lock:
            if subject_id in self._records:
                raise ValueError(f"health subject is already registered: {subject_id}")
            self._records[subject_id] = _HealthRecord(policy=policy)

    def heartbeat(self, subject_id: str) -> HealthSnapshot:
        """Record liveness without claiming health or changing reported state."""
        with self._lock:
            record = self._get_record(subject_id)
            self._observe(record)
            record.sequence += 1
            record.heartbeat_count += 1
            return self._snapshot(subject_id, record)

    def report(
        self,
        subject_id: str,
        state: HealthState,
        *,
        diagnostic_code: str | None = None,
    ) -> HealthSnapshot:
        if not isinstance(state, HealthState):
            raise TypeError("state must be a HealthState")
        if diagnostic_code is not None and (
            not isinstance(diagnostic_code, str)
            or not _SAFE_DIAGNOSTIC.fullmatch(diagnostic_code)
        ):
            raise ValueError("diagnostic_code must be a safe uppercase code")
        with self._lock:
            record = self._get_record(subject_id)
            self._observe(record)
            record.state = state
            record.diagnostic_code = diagnostic_code
            record.sequence += 1
            return self._snapshot(subject_id, record)

    def snapshot(self, subject_id: str) -> HealthSnapshot:
        with self._lock:
            return self._snapshot(subject_id, self._get_record(subject_id))

    def snapshots(self) -> tuple[HealthSnapshot, ...]:
        with self._lock:
            return tuple(
                self._snapshot(subject_id, record)
                for subject_id, record in self._records.items()
            )

    def _get_record(self, subject_id: str) -> _HealthRecord:
        try:
            return self._records[subject_id]
        except (KeyError, TypeError) as exc:
            raise KeyError(f"unknown health subject: {subject_id}") from exc

    def _observe(self, record: _HealthRecord) -> None:
        monotonic_now = self._monotonic_clock()
        if isinstance(monotonic_now, bool) or not isinstance(monotonic_now, (int, float)):
            raise ValueError("monotonic clock must return a finite number")
        try:
            monotonic_value = float(monotonic_now)
        except (OverflowError, ValueError) as exc:
            raise ValueError("monotonic clock must return a finite number") from exc
        if not math.isfinite(monotonic_value):
            raise ValueError("monotonic clock must return a finite number")
        wall_now = self._utc_clock()
        if not isinstance(wall_now, datetime) or wall_now.tzinfo is None:
            raise ValueError("UTC clock must return a timezone-aware datetime")
        record.observed_monotonic = monotonic_value
        record.observed_at_utc = wall_now.astimezone(UTC).isoformat().replace("+00:00", "Z")

    def _snapshot(self, subject_id: str, record: _HealthRecord) -> HealthSnapshot:
        age: float | None = None
        state = record.state
        if record.observed_monotonic is None:
            state = HealthState.UNKNOWN
        else:
            now = self._monotonic_clock()
            if isinstance(now, bool) or not isinstance(now, (int, float)):
                raise ValueError("monotonic clock must return a finite number")
            try:
                now_value = float(now)
            except (OverflowError, ValueError) as exc:
                raise ValueError("monotonic clock must return a finite number") from exc
            if not math.isfinite(now_value):
                raise ValueError("monotonic clock must return a finite number")
            age = max(0.0, now_value - record.observed_monotonic)
            if age >= record.policy.unhealthy_after_seconds:
                state = HealthState.UNHEALTHY
            elif age >= record.policy.degraded_after_seconds and state is not HealthState.UNHEALTHY:
                state = HealthState.DEGRADED
        return HealthSnapshot(
            subject_id=subject_id,
            state=state,
            sequence=record.sequence,
            heartbeat_count=record.heartbeat_count,
            last_observed_at_utc=record.observed_at_utc,
            age_seconds=age,
            diagnostic_code=record.diagnostic_code,
        )
