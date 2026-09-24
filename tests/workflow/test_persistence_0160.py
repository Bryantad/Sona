"""Durable workflow journal tests; reopening never runs step operations."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from sona.workflow import (
    RecoveryDecision,
    RetryMode,
    RetryPolicy,
    StepDefinition,
    StepState,
    TaskDefinition,
    WorkflowDefinition,
    WorkflowJournalStore,
    WorkflowLedger,
    WorkflowLedgerError,
    WorkflowPersistenceError,
    WorkflowState,
    new_step_id,
    new_task_id,
    new_workflow_id,
)


def _definition(operation: str = "build"):
    workflow_id = new_workflow_id()
    task_id = new_task_id()
    first, second = new_step_id(), new_step_id()
    definition = WorkflowDefinition(
        workflow_id,
        (
            TaskDefinition(
                task_id,
                (
                    StepDefinition(first, operation),
                    StepDefinition(
                        second,
                        "test",
                        depends_on=(first,),
                        retry=RetryPolicy(
                            mode=RetryMode.FIXED,
                            maximum_attempts=2,
                            delay_seconds=0.1,
                            maximum_delay_seconds=1.0,
                        ),
                    ),
                ),
            ),
        ),
    )
    return definition, first, second


def test_persistent_ledger_roundtrips_identity_dependencies_retry_and_terminal_state(tmp_path):
    store = WorkflowJournalStore(tmp_path / "state")
    definition, first, second = _definition()
    ledger = WorkflowLedger(store=store)
    ledger.create(definition)
    ledger.prepare(definition.workflow_id)
    ledger.start_step(definition.workflow_id, first)
    ledger.succeed_step(definition.workflow_id, first)
    ledger.start_step(definition.workflow_id, second)

    reopened = WorkflowLedger(store=WorkflowJournalStore(tmp_path / "state"))
    snapshots = reopened.restore()

    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot.definition == definition
    assert snapshot.state is WorkflowState.BLOCKED
    assert snapshot.steps[0].state is StepState.SUCCEEDED
    assert snapshot.steps[1].state is StepState.BLOCKED
    assert snapshot.steps[1].attempt_count == 1
    assert snapshot.steps[1].failure_code == "SONA-WORKFLOW-RECOVERY-REQUIRED"
    assert reopened.snapshot(definition.workflow_id) == snapshot
    assert (
        reopened.resume_step(
            definition.workflow_id,
            second,
            decision=RecoveryDecision.RETRY_FROM_START,
        ).state
        is WorkflowState.READY
    )
    assert reopened.start_step(definition.workflow_id, second).steps[1].attempt_count == 2


def test_schema1_workflow_journal_state_remains_readable(tmp_path):
    store = WorkflowJournalStore(tmp_path / "state")
    definition, _, _ = _definition()
    initial = WorkflowLedger().create(definition)
    legacy = replace(initial, schema_version=1)

    store.append(legacy, event_type="workflow.created")

    assert store.load_latest() == (legacy,)


def test_terminal_state_roundtrips_and_journal_is_append_only(tmp_path):
    store = WorkflowJournalStore(tmp_path / "state")
    definition, first, second = _definition()
    ledger = WorkflowLedger(store=store)
    ledger.create(definition)
    ledger.prepare(definition.workflow_id)
    ledger.start_step(definition.workflow_id, first)
    ledger.succeed_step(definition.workflow_id, first)
    ledger.start_step(definition.workflow_id, second)
    expected = ledger.succeed_step(definition.workflow_id, second)

    loaded = WorkflowJournalStore(tmp_path / "state").load_latest()

    assert loaded == (expected,)
    events = list(
        (tmp_path / "state" / "workflows" / str(definition.workflow_id)).glob("event-*.json")
    )
    assert len(events) == 6
    assert [path.name for path in events] == [f"event-{index:08d}.json" for index in range(1, 7)]


def test_restore_of_created_workflow_is_inert_and_does_not_start_operations(tmp_path):
    store = WorkflowJournalStore(tmp_path / "state")
    definition, _, _ = _definition()
    ledger = WorkflowLedger(store=store)
    created = ledger.create(definition)

    restored = WorkflowLedger(store=WorkflowJournalStore(tmp_path / "state")).restore()

    assert restored == (created,)
    assert restored[0].state is WorkflowState.CREATED
    assert all(step.attempt_count == 0 for step in restored[0].steps)


def test_interrupted_canceling_step_restores_blocked_not_as_canceled(tmp_path):
    store = WorkflowJournalStore(tmp_path / "state")
    definition, first, _ = _definition()
    ledger = WorkflowLedger(store=store)
    ledger.create(definition)
    ledger.prepare(definition.workflow_id)
    ledger.start_step(definition.workflow_id, first)
    ledger.cancel(definition.workflow_id)

    recovered = WorkflowLedger(store=WorkflowJournalStore(tmp_path / "state")).restore()[0]

    assert recovered.state is WorkflowState.BLOCKED
    assert recovered.steps[0].state is StepState.BLOCKED
    assert recovered.steps[0].attempt_count == 1
    assert recovered.steps[0].failure_code == "SONA-WORKFLOW-RECOVERY-REQUIRED"


def test_hash_chain_corruption_is_rejected_without_partial_restore(tmp_path):
    store = WorkflowJournalStore(tmp_path / "state")
    definition, _, _ = _definition()
    ledger = WorkflowLedger(store=store)
    ledger.create(definition)
    ledger.prepare(definition.workflow_id)
    event_path = (
        tmp_path / "state" / "workflows" / str(definition.workflow_id) / "event-00000002.json"
    )
    event = json.loads(event_path.read_text(encoding="utf-8"))
    event["event_type"] = "workflow.created"
    event_path.write_text(
        json.dumps(event, sort_keys=True, separators=(",", ":")), encoding="utf-8"
    )

    with pytest.raises(WorkflowPersistenceError, match="hash chain"):
        WorkflowLedger(store=WorkflowJournalStore(tmp_path / "state")).restore()


def test_noncanonical_or_truncated_event_fails_closed(tmp_path):
    store = WorkflowJournalStore(tmp_path / "state")
    definition, _, _ = _definition()
    WorkflowLedger(store=store).create(definition)
    event_path = (
        tmp_path / "state" / "workflows" / str(definition.workflow_id) / "event-00000001.json"
    )
    event_path.write_bytes(event_path.read_bytes() + b" ")

    with pytest.raises(WorkflowPersistenceError, match="canonical"):
        store.load_latest()


def test_rehashed_but_semantically_invalid_snapshot_fails_validation(tmp_path):
    store = WorkflowJournalStore(tmp_path / "state")
    definition, _, _ = _definition()
    WorkflowLedger(store=store).create(definition)
    event_path = (
        tmp_path / "state" / "workflows" / str(definition.workflow_id) / "event-00000001.json"
    )
    event = json.loads(event_path.read_text(encoding="utf-8"))
    event["snapshot"]["state"] = "ready"
    unsigned = dict(event)
    unsigned.pop("event_hash")
    canonical_unsigned = json.dumps(
        unsigned, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    event["event_hash"] = "sha256:" + hashlib.sha256(canonical_unsigned).hexdigest()
    event_path.write_text(
        json.dumps(event, sort_keys=True, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    with pytest.raises(WorkflowPersistenceError, match="workflow state is inconsistent"):
        store.load_latest()


def test_snapshot_cache_is_rebuilt_from_authoritative_journal(tmp_path):
    store = WorkflowJournalStore(tmp_path / "state")
    definition, _, _ = _definition()
    expected = WorkflowLedger(store=store).create(definition)
    directory = tmp_path / "state" / "workflows" / str(definition.workflow_id)
    (directory / "snapshot.json").unlink()

    assert store.load_latest() == (expected,)
    assert (directory / "snapshot.json").is_file()


def test_unpublished_empty_directory_and_staging_file_are_ignored_on_reopen(tmp_path):
    root = tmp_path / "state"
    store = WorkflowJournalStore(root)
    definition, _, _ = _definition()
    directory = root / "workflows" / str(definition.workflow_id)
    directory.mkdir()
    (directory / ".event-00000001.json.interrupted.tmp").write_bytes(b"partial")

    assert store.load_latest() == ()
    created = WorkflowLedger(store=store).create(definition)
    assert WorkflowJournalStore(root).load_latest() == (created,)


def test_invalid_workflow_operation_is_not_durably_serialized(tmp_path):
    store = WorkflowJournalStore(tmp_path / "state")
    definition, _, _ = _definition("process.execute: secret-value")
    ledger = WorkflowLedger(store=store)

    with pytest.raises(WorkflowPersistenceError, match="registered identifier"):
        ledger.create(definition)
    assert store.load_latest() == ()
    with pytest.raises(WorkflowLedgerError, match="unknown"):
        ledger.snapshot(definition.workflow_id)


def test_store_enforces_record_limit_before_committing_transition(tmp_path):
    store = WorkflowJournalStore(tmp_path / "state", maximum_record_bytes=512)
    definition, _, _ = _definition()
    ledger = WorkflowLedger(store=store)

    with pytest.raises(WorkflowPersistenceError, match="byte limit"):
        ledger.create(definition)
    assert store.load_latest() == ()
    with pytest.raises(WorkflowLedgerError, match="unknown"):
        ledger.snapshot(definition.workflow_id)


def test_persistence_failure_rolls_back_an_in_memory_transition(tmp_path):
    class FailingStore:
        def append(self, snapshot, *, event_type):
            if event_type == "step.started":
                raise WorkflowPersistenceError("injected journal failure")

        def load_latest(self):
            return ()

    definition, first, _ = _definition()
    ledger = WorkflowLedger(store=FailingStore())
    ledger.create(definition)
    ledger.prepare(definition.workflow_id)
    before = ledger.snapshot(definition.workflow_id)

    with pytest.raises(WorkflowPersistenceError, match="injected"):
        ledger.start_step(definition.workflow_id, first)

    assert ledger.snapshot(definition.workflow_id) == before
