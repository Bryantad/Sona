"""Stable public memory-model surface for Sona runtime cognition.

This package exposes durable memory models, enums, and narrow payload/schema
helpers that are safe to treat as the default public surface.

Host-oriented kernels live in ``sona.runtime.memory.advanced``.
Goal continuation, inference, and checkpoint orchestration live in
``sona.runtime.memory.internal``.
"""

from .enums import (
    CheckpointState,
    ClassificationTier,
    GoalState,
    ProcedureReviewState,
    RetentionState,
    TrustState,
)
from .ids import make_prefixed_id, utc_now
from .models import (
    AgentCheckpoint,
    AgentStateProfile,
    Episode,
    Fact,
    Goal,
    MemoryClaim,
    MemoryLink,
    MemoryReceiptRef,
    Procedure,
)
from .schema import SCHEMA_VERSION
from .payloads import normalize_episode_payload, supported_episode_kinds

__all__ = [
    "AgentCheckpoint",
    "AgentStateProfile",
    "CheckpointState",
    "ClassificationTier",
    "Episode",
    "Fact",
    "Goal",
    "GoalState",
    "MemoryClaim",
    "MemoryLink",
    "MemoryReceiptRef",
    "Procedure",
    "ProcedureReviewState",
    "RetentionState",
    "SCHEMA_VERSION",
    "TrustState",
    "normalize_episode_payload",
    "supported_episode_kinds",
]
