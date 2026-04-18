"""Read-mostly compliance reporting for the runtime memory subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .audit import AuditKernel, AuditSummary
from .enums import ClassificationTier, RetentionState
from .ids import utc_now
from .policy import PolicyKernel, default_runtime_policy
from .storage import MemoryStore


@dataclass(frozen=True, slots=True)
class ComplianceViolation:
    object_type: str
    object_id: str
    rule_code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ComplianceReport:
    generated_at: str
    policy_fingerprint: str
    total_records_scanned: int
    violations: list[ComplianceViolation]
    retention_compliance: dict[str, float]
    classification_compliance: dict[str, float]
    provenance_completeness: dict[str, float]
    audit_summary: AuditSummary | None = None

    @property
    def is_compliant(self) -> bool:
        return len(self.violations) == 0


class ComplianceReporter:
    """Generate compliance reports against policy and audit state.

    This class is strictly read-only — it queries the memory store and
    audit log but never modifies them.
    """

    def __init__(
        self,
        store: MemoryStore,
        policy_kernel: PolicyKernel | None = None,
        audit_kernel: AuditKernel | None = None,
    ):
        self.store = store
        self.policy_kernel = policy_kernel or PolicyKernel(default_runtime_policy())
        self.audit_kernel = audit_kernel

    def generate_report(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        scan_limit: int = 500,
    ) -> ComplianceReport:
        violations: list[ComplianceViolation] = []
        total_scanned = 0
        retention_stats: dict[str, dict[str, int]] = {}
        classification_stats: dict[str, dict[str, int]] = {}
        provenance_stats: dict[str, dict[str, int]] = {}

        for object_type, query_fn, classification_attr, receipt_attr in self._scan_targets():
            records = query_fn(
                agent_id=agent_id, session_id=session_id, limit=scan_limit,
            )
            total_scanned += len(records)
            type_key = object_type
            retention_stats.setdefault(type_key, {"compliant": 0, "total": 0})
            classification_stats.setdefault(type_key, {"compliant": 0, "total": 0})
            provenance_stats.setdefault(type_key, {"has_refs": 0, "total": 0})

            for record in records:
                retention_stats[type_key]["total"] += 1
                classification_stats[type_key]["total"] += 1
                provenance_stats[type_key]["total"] += 1

                # Retention compliance
                retention = getattr(record, "retention_state", None)
                if retention == RetentionState.DELETED:
                    violations.append(ComplianceViolation(
                        object_type=type_key,
                        object_id=record.id,
                        rule_code="retention.deleted_present",
                        message="Deleted record still present in active query results",
                    ))
                else:
                    retention_stats[type_key]["compliant"] += 1

                # Classification compliance
                classification = getattr(record, classification_attr, None)
                if classification is not None:
                    max_class = self.policy_kernel.policy.classification_policy.max_classification
                    if self._classification_rank(classification) > self._classification_rank(max_class):
                        violations.append(ComplianceViolation(
                            object_type=type_key,
                            object_id=record.id,
                            rule_code="classification.exceeds_policy",
                            message=(
                                f"{type_key.title()} classification "
                                f"'{self._enum_value(classification)}' exceeds "
                                f"policy max '{max_class.value}'"
                            ),
                            details={
                                "classification": self._enum_value(classification),
                                "max_classification": max_class.value,
                            },
                        ))
                    else:
                        classification_stats[type_key]["compliant"] += 1
                else:
                    classification_stats[type_key]["compliant"] += 1

                # Provenance completeness
                refs = getattr(record, receipt_attr, [])
                if refs:
                    provenance_stats[type_key]["has_refs"] += 1

        retention_compliance = {
            k: v["compliant"] / v["total"] if v["total"] else 1.0
            for k, v in retention_stats.items()
        }
        classification_compliance = {
            k: v["compliant"] / v["total"] if v["total"] else 1.0
            for k, v in classification_stats.items()
        }
        provenance_completeness = {
            k: v["has_refs"] / v["total"] if v["total"] else 1.0
            for k, v in provenance_stats.items()
        }

        audit_summary: AuditSummary | None = None
        if self.audit_kernel is not None:
            audit_summary = self.audit_kernel.summarize()

        return ComplianceReport(
            generated_at=utc_now(),
            policy_fingerprint=self.policy_kernel.resolve_policy_fingerprint(),
            total_records_scanned=total_scanned,
            violations=violations,
            retention_compliance=retention_compliance,
            classification_compliance=classification_compliance,
            provenance_completeness=provenance_completeness,
            audit_summary=audit_summary,
        )

    def list_violations(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        scan_limit: int = 500,
    ) -> list[ComplianceViolation]:
        report = self.generate_report(
            agent_id=agent_id, session_id=session_id, scan_limit=scan_limit,
        )
        return report.violations

    def _scan_targets(self) -> list[tuple[str, Any, str, str]]:
        return [
            ("episode", self.store.query_episodes, "classification", "receipt_refs"),
            ("claim", self.store.query_claims, "classification", "receipt_refs"),
            ("fact", self.store.query_facts, "classification", "receipt_refs"),
            ("procedure", self.store.query_procedures, "classification", "receipt_refs"),
        ]

    @staticmethod
    def _classification_rank(value: Any) -> int:
        if isinstance(value, ClassificationTier):
            tier = value
        elif isinstance(value, str):
            try:
                tier = ClassificationTier(value.strip().lower())
            except ValueError:
                return 2
        else:
            return 2
        return {
            ClassificationTier.PUBLIC: 1,
            ClassificationTier.INTERNAL: 2,
            ClassificationTier.SENSITIVE: 3,
        }[tier]

    @staticmethod
    def _enum_value(value: Any) -> str:
        return value.value if hasattr(value, "value") else str(value)


__all__ = [
    "ComplianceReport",
    "ComplianceReporter",
    "ComplianceViolation",
]
