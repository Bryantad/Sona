"""Tests for sona.runtime.memory.compliance — read-only compliance reporting."""

from sona.runtime.memory import ClassificationTier, Episode
from sona.runtime.memory.audit import AuditKernel
from sona.runtime.memory.compliance import (
    ComplianceReport,
    ComplianceReporter,
    ComplianceViolation,
)
from sona.runtime.memory.policy import (
    ClassificationPolicy,
    MemoryPolicy,
    PolicyKernel,
    RetentionPolicy,
    default_runtime_policy,
)
from sona.runtime.memory.sqlite_store import SQLiteMemoryStore


def _make_store(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    store.initialize()
    return store


def _save_episode(store, *, classification=ClassificationTier.INTERNAL, **kw):
    defaults = dict(
        agent_id="agent-1",
        session_id="sess-1",
        kind="working_memory_update",
        source_type="runtime",
        payload={"key": "value"},
        classification=classification,
    )
    defaults.update(kw)
    ep = Episode(**defaults)
    return store.append_episode(ep)


def test_generate_report_clean(tmp_path):
    store = _make_store(tmp_path)
    _save_episode(store, classification=ClassificationTier.INTERNAL)

    reporter = ComplianceReporter(store)
    report = reporter.generate_report()

    assert isinstance(report, ComplianceReport)
    assert report.is_compliant
    assert report.total_records_scanned >= 1
    assert report.policy_fingerprint


def test_generate_report_with_audit(tmp_path):
    store = _make_store(tmp_path)
    _save_episode(store)
    audit = AuditKernel(store)
    audit.log_action(
        subject_type="episode", subject_id="ep-x",
        action="episode_appended", actor_id="agent-1",
    )

    reporter = ComplianceReporter(store, audit_kernel=audit)
    report = reporter.generate_report()

    assert report.audit_summary is not None
    assert report.audit_summary.total_events == 1


def test_generate_report_without_audit(tmp_path):
    store = _make_store(tmp_path)
    _save_episode(store)

    reporter = ComplianceReporter(store)
    report = reporter.generate_report()

    assert report.audit_summary is None


def test_classification_exceeds_policy_generates_violation(tmp_path):
    store = _make_store(tmp_path)
    _save_episode(store, classification=ClassificationTier.SENSITIVE)

    policy = MemoryPolicy(
        retention_policy={"episode": RetentionPolicy()},
        classification_policy=ClassificationPolicy(
            max_classification=ClassificationTier.INTERNAL,
        ),
    )
    kernel = PolicyKernel(policy)
    reporter = ComplianceReporter(store, policy_kernel=kernel)

    report = reporter.generate_report()

    assert not report.is_compliant
    assert len(report.violations) >= 1
    violation = report.violations[0]
    assert isinstance(violation, ComplianceViolation)
    assert violation.rule_code == "classification.exceeds_policy"
    assert violation.object_type == "episode"


def test_classification_within_policy_is_compliant(tmp_path):
    store = _make_store(tmp_path)
    _save_episode(store, classification=ClassificationTier.INTERNAL)

    policy = MemoryPolicy(
        retention_policy={"episode": RetentionPolicy()},
        classification_policy=ClassificationPolicy(
            max_classification=ClassificationTier.SENSITIVE,
        ),
    )
    kernel = PolicyKernel(policy)
    reporter = ComplianceReporter(store, policy_kernel=kernel)

    report = reporter.generate_report()

    assert report.is_compliant


def test_list_violations_convenience(tmp_path):
    store = _make_store(tmp_path)
    _save_episode(store, classification=ClassificationTier.SENSITIVE)

    policy = MemoryPolicy(
        retention_policy={"episode": RetentionPolicy()},
        classification_policy=ClassificationPolicy(
            max_classification=ClassificationTier.PUBLIC,
        ),
    )
    kernel = PolicyKernel(policy)
    reporter = ComplianceReporter(store, policy_kernel=kernel)

    violations = reporter.list_violations()
    assert len(violations) >= 1
    assert violations[0].rule_code == "classification.exceeds_policy"


def test_empty_store_is_compliant(tmp_path):
    store = _make_store(tmp_path)

    reporter = ComplianceReporter(store)
    report = reporter.generate_report()

    assert report.is_compliant
    assert report.total_records_scanned == 0


def test_retention_compliance_ratio(tmp_path):
    store = _make_store(tmp_path)
    _save_episode(store)
    _save_episode(store)

    reporter = ComplianceReporter(store)
    report = reporter.generate_report()

    assert "episode" in report.retention_compliance
    assert report.retention_compliance["episode"] == 1.0


def test_report_policy_fingerprint_matches_kernel(tmp_path):
    store = _make_store(tmp_path)
    kernel = PolicyKernel(default_runtime_policy())

    reporter = ComplianceReporter(store, policy_kernel=kernel)
    report = reporter.generate_report()

    assert report.policy_fingerprint == kernel.resolve_policy_fingerprint()
