from sona.runtime.memory import (
    AgentCheckpoint,
    CheckpointState,
    ClassificationTier,
    Episode,
    MemoryReceiptRef,
    RetentionState,
)
from sona.runtime.memory.advanced import (
    CheckpointPolicy,
    ClassificationPolicy,
    MemoryPolicy,
    PolicyKernel,
    RetentionPolicy,
    ScopePolicy,
    default_runtime_policy,
)


def test_default_runtime_policy_fingerprint_is_deterministic():
    first = PolicyKernel(default_runtime_policy()).export_snapshot()
    second = PolicyKernel(default_runtime_policy()).export_snapshot()

    assert first.payload == second.payload
    assert first.fingerprint == second.fingerprint


def test_policy_kernel_denies_sensitive_episode_when_max_is_internal():
    policy = MemoryPolicy(
        retention_policy={"episode": RetentionPolicy()},
        classification_policy=ClassificationPolicy(
            max_classification=ClassificationTier.INTERNAL,
        ),
    )
    kernel = PolicyKernel(policy)
    episode = Episode(
        agent_id="agent",
        session_id="session",
        kind="working_memory_update",
        source_type="runtime",
        payload={"action": "store", "key": "x"},
        classification=ClassificationTier.SENSITIVE,
    )

    decision = kernel.validate_episode_append(episode)

    assert decision.allowed is False
    assert decision.violation is not None
    assert decision.violation.rule_code == "classification.max_exceeded"


def test_policy_kernel_denies_project_scope_without_workspace_when_required():
    policy = MemoryPolicy(
        retention_policy={"episode": RetentionPolicy()},
        scope_policy=ScopePolicy(require_workspace_for_project=True),
    )
    kernel = PolicyKernel(policy)
    episode = Episode(
        agent_id="agent",
        session_id="session",
        kind="working_memory_update",
        source_type="runtime",
        payload={"action": "store", "key": "x"},
        project_id="proj-1",
    )

    decision = kernel.validate_episode_append(episode)

    assert decision.allowed is False
    assert decision.violation is not None
    assert decision.violation.rule_code == "scope.workspace_required_for_project"


def test_policy_kernel_denies_direct_delete_when_archive_required():
    policy = MemoryPolicy(
        retention_policy={
            "fact": RetentionPolicy(require_archive_before_delete=True),
        }
    )
    kernel = PolicyKernel(policy)

    decision = kernel.validate_retention_transition(
        "fact",
        RetentionState.ACTIVE,
        RetentionState.DELETED,
    )

    assert decision.allowed is False
    assert decision.violation is not None
    assert decision.violation.rule_code == "retention.archive_required_before_delete"


def test_policy_kernel_denies_invalidated_checkpoint_restore():
    kernel = PolicyKernel(
        MemoryPolicy(
            retention_policy={},
            checkpoint_policy=CheckpointPolicy(allow_restore_invalidated=False),
        )
    )
    checkpoint = AgentCheckpoint(
        agent_id="agent",
        session_id="session",
        working_state_blob={},
        state=CheckpointState.INVALIDATED,
    )

    decision = kernel.validate_checkpoint_restore(checkpoint, agent_id="agent")

    assert decision.allowed is False
    assert decision.violation is not None
    assert decision.violation.rule_code == "checkpoint.invalidated_restore_denied"


def test_policy_kernel_allows_missing_receipt_fingerprint_by_default():
    kernel = PolicyKernel(default_runtime_policy())
    checkpoint = AgentCheckpoint(
        agent_id="agent",
        session_id="session",
        working_state_blob={},
        last_receipt_ref=MemoryReceiptRef(
            receipt_id="r1",
            event_kind_or_path="execution.events[0]",
        ),
    )

    decision = kernel.validate_checkpoint_restore(checkpoint, agent_id="agent")

    assert decision.allowed is True
    assert decision.warnings