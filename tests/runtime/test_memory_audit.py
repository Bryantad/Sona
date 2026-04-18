"""Tests for sona.runtime.memory.audit — append-only governance log."""

from sona.runtime.memory.audit import AuditEvent, AuditKernel, AuditSummary
from sona.runtime.memory.sqlite_store import SQLiteMemoryStore


def _make_store(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    store.initialize()
    return store


def test_log_action_returns_audit_event(tmp_path):
    store = _make_store(tmp_path)
    kernel = AuditKernel(store)

    event = kernel.log_action(
        subject_type="episode",
        subject_id="ep-001",
        action="episode_appended",
        actor_id="agent-1",
    )

    assert isinstance(event, AuditEvent)
    assert event.subject_type == "episode"
    assert event.subject_id == "ep-001"
    assert event.action == "episode_appended"
    assert event.actor_id == "agent-1"
    assert event.id.startswith("audit_")
    assert event.timestamp


def test_log_action_persists_event(tmp_path):
    store = _make_store(tmp_path)
    kernel = AuditKernel(store)

    kernel.log_action(
        subject_type="episode",
        subject_id="ep-001",
        action="episode_appended",
        actor_id="agent-1",
    )

    assert kernel.count_events() == 1


def test_log_action_with_details_and_policy_context(tmp_path):
    store = _make_store(tmp_path)
    kernel = AuditKernel(store)

    event = kernel.log_action(
        subject_type="episode",
        subject_id="ep-002",
        action="episode_append_denied",
        actor_id="agent-1",
        policy_fingerprint="fp-abc",
        details={"reason": "classification exceeded"},
        policy_context={"rule": "classification.max_exceeded"},
    )

    assert event.policy_fingerprint == "fp-abc"
    assert event.details["reason"] == "classification exceeded"
    assert event.policy_context["rule"] == "classification.max_exceeded"

    trail = kernel.query_audit_trail("ep-002")
    assert len(trail) == 1
    assert trail[0].details["reason"] == "classification exceeded"
    assert trail[0].policy_context["rule"] == "classification.max_exceeded"


def test_query_audit_trail(tmp_path):
    store = _make_store(tmp_path)
    kernel = AuditKernel(store)

    kernel.log_action(
        subject_type="episode", subject_id="ep-001",
        action="episode_appended", actor_id="agent-1",
    )
    kernel.log_action(
        subject_type="episode", subject_id="ep-001",
        action="retention_transition", actor_id="agent-1",
    )
    kernel.log_action(
        subject_type="episode", subject_id="ep-002",
        action="episode_appended", actor_id="agent-1",
    )

    trail = kernel.query_audit_trail("ep-001")
    assert len(trail) == 2
    assert all(e.subject_id == "ep-001" for e in trail)


def test_query_by_actor(tmp_path):
    store = _make_store(tmp_path)
    kernel = AuditKernel(store)

    kernel.log_action(
        subject_type="episode", subject_id="ep-001",
        action="episode_appended", actor_id="agent-A",
    )
    kernel.log_action(
        subject_type="episode", subject_id="ep-002",
        action="episode_appended", actor_id="agent-B",
    )

    results = kernel.query_by_actor("agent-A")
    assert len(results) == 1
    assert results[0].actor_id == "agent-A"


def test_query_by_action(tmp_path):
    store = _make_store(tmp_path)
    kernel = AuditKernel(store)

    kernel.log_action(
        subject_type="episode", subject_id="ep-001",
        action="episode_appended", actor_id="agent-1",
    )
    kernel.log_action(
        subject_type="episode", subject_id="ep-002",
        action="episode_append_denied", actor_id="agent-1",
    )
    kernel.log_action(
        subject_type="episode", subject_id="ep-003",
        action="episode_appended", actor_id="agent-1",
    )

    results = kernel.query_by_action("episode_appended")
    assert len(results) == 2
    assert all(e.action == "episode_appended" for e in results)


def test_count_events(tmp_path):
    store = _make_store(tmp_path)
    kernel = AuditKernel(store)

    assert kernel.count_events() == 0

    kernel.log_action(
        subject_type="episode", subject_id="ep-001",
        action="a", actor_id="agent-1",
    )
    kernel.log_action(
        subject_type="fact", subject_id="fact-001",
        action="b", actor_id="agent-1",
    )

    assert kernel.count_events() == 2


def test_summarize(tmp_path):
    store = _make_store(tmp_path)
    kernel = AuditKernel(store)

    kernel.log_action(
        subject_type="episode", subject_id="ep-001",
        action="episode_appended", actor_id="agent-A",
    )
    kernel.log_action(
        subject_type="fact", subject_id="fact-001",
        action="retention_transition", actor_id="agent-B",
    )

    summary = kernel.summarize()
    assert isinstance(summary, AuditSummary)
    assert summary.total_events == 2
    assert summary.actions["episode_appended"] == 1
    assert summary.actions["retention_transition"] == 1
    assert summary.subject_types["episode"] == 1
    assert summary.subject_types["fact"] == 1
    assert summary.actors["agent-A"] == 1
    assert summary.actors["agent-B"] == 1
    assert summary.first_timestamp is not None
    assert summary.last_timestamp is not None


def test_summarize_empty(tmp_path):
    store = _make_store(tmp_path)
    kernel = AuditKernel(store)

    summary = kernel.summarize()
    assert summary.total_events == 0
    assert summary.first_timestamp is None
    assert summary.last_timestamp is None


def test_verify_episode_immutability_true(tmp_path):
    store = _make_store(tmp_path)
    kernel = AuditKernel(store)

    kernel.log_action(
        subject_type="episode", subject_id="ep-001",
        action="episode_appended", actor_id="agent-1",
    )

    assert kernel.verify_episode_immutability("ep-001") is True


def test_verify_episode_immutability_false(tmp_path):
    store = _make_store(tmp_path)
    kernel = AuditKernel(store)

    kernel.log_action(
        subject_type="episode", subject_id="ep-001",
        action="episode_appended", actor_id="agent-1",
    )
    kernel.log_action(
        subject_type="episode", subject_id="ep-001",
        action="retention_transition", actor_id="agent-1",
    )

    assert kernel.verify_episode_immutability("ep-001") is False


def test_export_forensic_report_unfiltered(tmp_path):
    store = _make_store(tmp_path)
    kernel = AuditKernel(store)

    kernel.log_action(
        subject_type="episode", subject_id="ep-001",
        action="episode_appended", actor_id="agent-1",
    )
    kernel.log_action(
        subject_type="fact", subject_id="fact-001",
        action="retention_transition", actor_id="agent-2",
    )

    report = kernel.export_forensic_report()
    assert report["report_type"] == "forensic_audit"
    assert report["total_events"] == 2
    assert len(report["events"]) == 2


def test_export_forensic_report_filtered_by_subject(tmp_path):
    store = _make_store(tmp_path)
    kernel = AuditKernel(store)

    kernel.log_action(
        subject_type="episode", subject_id="ep-001",
        action="episode_appended", actor_id="agent-1",
    )
    kernel.log_action(
        subject_type="fact", subject_id="fact-001",
        action="episode_appended", actor_id="agent-1",
    )

    report = kernel.export_forensic_report(subject_id="ep-001")
    assert report["total_events"] == 1
    assert report["events"][0]["subject_id"] == "ep-001"


def test_export_forensic_report_filtered_by_action(tmp_path):
    store = _make_store(tmp_path)
    kernel = AuditKernel(store)

    kernel.log_action(
        subject_type="episode", subject_id="ep-001",
        action="episode_appended", actor_id="agent-1",
    )
    kernel.log_action(
        subject_type="episode", subject_id="ep-002",
        action="retention_transition", actor_id="agent-1",
    )

    report = kernel.export_forensic_report(action="retention_transition")
    assert report["total_events"] == 1
    assert report["events"][0]["action"] == "retention_transition"


def test_query_audit_trail_limit(tmp_path):
    store = _make_store(tmp_path)
    kernel = AuditKernel(store)

    for i in range(10):
        kernel.log_action(
            subject_type="episode", subject_id="ep-001",
            action=f"action_{i}", actor_id="agent-1",
        )

    trail = kernel.query_audit_trail("ep-001", limit=3)
    assert len(trail) == 3


def test_multiple_audit_kernels_share_schema(tmp_path):
    """Two AuditKernel instances on the same store share the audit_log table."""
    store = _make_store(tmp_path)
    k1 = AuditKernel(store)
    k2 = AuditKernel(store)

    k1.log_action(
        subject_type="episode", subject_id="ep-001",
        action="a", actor_id="agent-1",
    )

    assert k2.count_events() == 1
