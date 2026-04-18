"""Canonical enums for the persistent memory subsystem."""

from __future__ import annotations

from enum import Enum


class _StrEnum(str, Enum):
    def __str__(self) -> str:  # pragma: no cover - trivial wrapper
        return self.value


class TrustState(_StrEnum):
    UNVERIFIED = "unverified"
    OBSERVED = "observed"
    DERIVED = "derived"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"


class ClassificationTier(_StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"


class RetentionState(_StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    FORGOTTEN = "forgotten"
    DELETED = "deleted"


class GoalState(_StrEnum):
    OPEN = "open"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class CheckpointState(_StrEnum):
    CURRENT = "current"
    SUPERSEDED = "superseded"
    INVALIDATED = "invalidated"


class ProcedureReviewState(_StrEnum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"
