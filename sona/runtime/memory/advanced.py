"""Advanced host-integration runtime memory surfaces.

These symbols support embedding, inspection, promotion, retrieval, and storage
integration. They are valid extension points for advanced host usage, but they
are not the default language-facing entrypoint for Sona.
"""

from .audit import AuditEvent, AuditKernel, AuditSummary
from .compliance import ComplianceReport, ComplianceReporter, ComplianceViolation
from .consolidation import (
    CandidateClaim,
    CandidateFact,
    ConsolidationKernel,
    ConsolidationReport,
    DuplicateClaimGroup,
    NoiseFlag,
)
from .inspection import InspectionKernel, MemoryInspection, ProvenanceTrace
from .intake import RuntimeExecutionIdentity, RuntimeMemoryIntake
from .policy import (
    CheckpointPolicy,
    ClassificationPolicy,
    MemoryPolicy,
    PolicyDecision,
    PolicyKernel,
    PolicySnapshot,
    PolicyViolation,
    PromotionPolicy,
    RetentionPolicy,
    ScopePolicy,
    default_runtime_policy,
)
from .promotion import PromotionKernel
from .retrieval import RetrievedMemory, RetrievalExplanation, RetrievalKernel
from .schema import SCHEMA_STATEMENTS, SCHEMA_VERSION
from .sqlite_store import SQLiteMemoryStore
from .storage import MemoryStore

__all__ = [
    "AuditEvent",
    "AuditKernel",
    "AuditSummary",
    "CandidateClaim",
    "CandidateFact",
    "ComplianceReport",
    "ComplianceReporter",
    "ComplianceViolation",
    "ConsolidationKernel",
    "ConsolidationReport",
    "DuplicateClaimGroup",
    "InspectionKernel",
    "MemoryPolicy",
    "MemoryInspection",
    "MemoryStore",
    "NoiseFlag",
    "PolicyDecision",
    "PolicyKernel",
    "PolicySnapshot",
    "PolicyViolation",
    "PromotionKernel",
    "PromotionPolicy",
    "ProvenanceTrace",
    "RetentionPolicy",
    "RetrievedMemory",
    "RetrievalExplanation",
    "RetrievalKernel",
    "RuntimeExecutionIdentity",
    "RuntimeMemoryIntake",
    "SCHEMA_STATEMENTS",
    "SCHEMA_VERSION",
    "ScopePolicy",
    "SQLiteMemoryStore",
    "CheckpointPolicy",
    "ClassificationPolicy",
    "default_runtime_policy",
]