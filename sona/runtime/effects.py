"""Bounded structured effect records with separate authorization and result."""

from __future__ import annotations

import re
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from .contracts import EffectClass, EffectDecision, EffectResult

_SAFE_RESOURCE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_MAX_EFFECT_RECORDS = 65_536


class EffectJournalFullError(OverflowError):
    """Raised rather than silently discarding bounded effect evidence."""


@dataclass(frozen=True, slots=True)
class EffectRecord:
    sequence: int
    attempt_id: str
    effect: EffectClass
    resource_ref: str
    decision: EffectDecision
    result: EffectResult
    capability_id: str | None
    occurred_at_utc: str


class EffectJournal:
    """In-memory bounded audit of supplied decisions and observed results.

    This records caller-provided observations; it does not itself authorize or
    perform an operating-system effect.
    """

    def __init__(self, *, maximum_records: int = 4096) -> None:
        if (
            isinstance(maximum_records, bool)
            or not isinstance(maximum_records, int)
            or not 1 <= maximum_records <= _MAX_EFFECT_RECORDS
        ):
            raise ValueError("maximum_records must be between 1 and 65536")
        self.maximum_records = maximum_records
        self._records: list[EffectRecord] = []
        self._lock = threading.Lock()

    def record(
        self,
        effect: EffectClass,
        resource_ref: str,
        decision: EffectDecision,
        result: EffectResult,
        *,
        capability_id: str | None = None,
        occurred_at: datetime | None = None,
        attempt_id: str | None = None,
    ) -> EffectRecord:
        if not isinstance(effect, EffectClass):
            raise TypeError("effect must be an EffectClass")
        if not isinstance(resource_ref, str) or not _SAFE_RESOURCE_REF.fullmatch(resource_ref):
            raise ValueError("resource_ref must be a safe opaque identifier, not a raw path")
        if not isinstance(decision, EffectDecision):
            raise TypeError("decision must be an EffectDecision")
        if not isinstance(result, EffectResult):
            raise TypeError("result must be an EffectResult")
        if decision is EffectDecision.DENIED and result is not EffectResult.NOT_ATTEMPTED:
            raise ValueError("a denied effect must be recorded as not_attempted")
        if decision is EffectDecision.UNKNOWN and result not in {
            EffectResult.UNKNOWN,
            EffectResult.NOT_ATTEMPTED,
        }:
            raise ValueError("an unknown decision cannot claim a completed effect result")
        record_id = attempt_id or str(uuid.uuid4())
        _validate_uuid(record_id, "attempt_id")
        if capability_id is not None:
            _validate_uuid(capability_id, "capability_id")
        timestamp = occurred_at or datetime.now(UTC)
        if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
            raise ValueError("occurred_at must be a timezone-aware datetime")
        occurred_at_utc = timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z")

        with self._lock:
            if len(self._records) >= self.maximum_records:
                raise EffectJournalFullError("effect journal is full; no record was discarded")
            record = EffectRecord(
                sequence=len(self._records) + 1,
                attempt_id=record_id,
                effect=effect,
                resource_ref=resource_ref,
                decision=decision,
                result=result,
                capability_id=capability_id,
                occurred_at_utc=occurred_at_utc,
            )
            self._records.append(record)
            return record

    def snapshot(self) -> tuple[EffectRecord, ...]:
        with self._lock:
            return tuple(self._records)


def _validate_uuid(value: str, field_name: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a UUID")
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"{field_name} must be a UUID") from exc
