from pathlib import Path

import pytest

from sona.ast_nodes import IntentStatement
from sona.interpreter import SonaRuntimeError, SonaUnifiedInterpreter
from sona.runtime.memory import ClassificationTier
from sona.runtime.memory.advanced import (
    ClassificationPolicy,
    MemoryPolicy,
    PolicyKernel,
    RuntimeExecutionIdentity,
    RuntimeMemoryIntake,
)
from sona.receipts import (
    append_receipt_event,
    clear_active_receipt,
    set_active_receipt,
)


class _ValueExpr:
    def __init__(self, value):
        self.value = value

    def evaluate(self, _vm):
        return self.value


def _episode_store_path(project_root: Path) -> Path:
    return project_root / ".sona" / "runtime_memory.db"


def test_intent_statement_persists_runtime_episode_with_identity(tmp_path):
    interpreter = SonaUnifiedInterpreter(project_root=tmp_path)
    statement = IntentStatement(
        body={
            "goal": _ValueExpr("Ship runtime intake"),
            "constraints": _ValueExpr(["thin slice"]),
        }
    )

    statement.execute(interpreter)

    episodes = interpreter.runtime_memory_store.query_episodes(
        agent_id=interpreter.runtime_agent_id,
        session_id=interpreter.runtime_session_id,
    )
    intent_episode = next(ep for ep in episodes if ep.kind == "intent_recorded")

    assert intent_episode.project_id == interpreter.runtime_project_id
    assert intent_episode.workspace_id == interpreter.runtime_workspace_id
    assert intent_episode.payload["goal"] == "Ship runtime intake"
    assert _episode_store_path(tmp_path).exists()


def test_interpret_persists_user_input_episode(tmp_path):
    interpreter = SonaUnifiedInterpreter(project_root=tmp_path)

    interpreter.interpret("x = 1\n", filename="direct_input.sona")

    episodes = interpreter.runtime_memory_store.query_episodes(
        agent_id=interpreter.runtime_agent_id,
        session_id=interpreter.runtime_session_id,
    )
    user_input = next(ep for ep in episodes if ep.kind == "user_input")

    assert user_input.payload["filename"] == "direct_input.sona"
    assert user_input.payload["line_count"] == 1
    assert user_input.agent_id == interpreter.runtime_agent_id


def test_receipt_linkage_is_attached_for_runtime_episode(tmp_path):
    interpreter = SonaUnifiedInterpreter(project_root=tmp_path)
    receipt_ctx = {
        "receipt_id": "rcpt_runtime_001",
        "receipt_hash": "a" * 64,
        "header": {"policy_fingerprint": "policy-1"},
        "execution": {
            "events": [
                {"t": 0, "kind": "start", "classification": "internal"},
                {"t": 1, "kind": "end", "classification": "internal"},
            ]
        },
    }
    set_active_receipt(receipt_ctx)
    try:
        append_receipt_event("tool_result", payload={"tool": "pytest"})
        episode = interpreter.record_memory_episode(
            kind="tool_observation",
            source_type="runtime",
            importance=0.8,
            payload={"tool": "pytest", "ok": True},
        )
    finally:
        clear_active_receipt()

    assert episode is not None
    refs = interpreter.runtime_memory_store.get_receipt_refs("episode", episode.id)
    assert len(refs) == 1
    assert refs[0].receipt_id == "rcpt_runtime_001"
    assert refs[0].event_kind_or_path == "execution.events[2]"
    assert refs[0].receipt_hash == "a" * 64


def test_importance_gating_skips_low_importance_episode(tmp_path):
    interpreter = SonaUnifiedInterpreter(project_root=tmp_path)

    stored = interpreter.record_memory_episode(
        kind="trace_noise",
        source_type="runtime",
        importance=0.05,
        payload={"detail": "ignore me"},
    )

    episodes = interpreter.runtime_memory_store.query_episodes(
        agent_id=interpreter.runtime_agent_id,
        session_id=interpreter.runtime_session_id,
    )
    assert stored is None
    assert episodes == []


def test_interpret_failure_persists_failure_episode(tmp_path):
    interpreter = SonaUnifiedInterpreter(project_root=tmp_path)

    with pytest.raises(SonaRuntimeError):
        interpreter.interpret("1 / 0", filename="failure_case.sona")

    episodes = interpreter.runtime_memory_store.query_episodes(
        agent_id=interpreter.runtime_agent_id,
        session_id=interpreter.runtime_session_id,
    )
    failure_episode = next(ep for ep in episodes if ep.kind == "interpret_failure")

    assert failure_episode.payload["filename"] == "failure_case.sona"
    assert failure_episode.payload["error_type"] == "ZeroDivisionError"


def test_runtime_intake_rejects_episode_that_violates_policy(tmp_path):
    interpreter = SonaUnifiedInterpreter(project_root=tmp_path)
    policy = MemoryPolicy(
        retention_policy={"episode": interpreter.runtime_memory_policy.retention_policy["episode"]},
        classification_policy=ClassificationPolicy(
            max_classification=ClassificationTier.INTERNAL,
        ),
    )
    intake = RuntimeMemoryIntake(
        interpreter.runtime_memory_store,
        policy_kernel=PolicyKernel(policy),
    )

    try:
        intake.append_episode(
            kind="working_memory_update",
            source_type="runtime",
            payload={"action": "store", "key": "restricted"},
            execution_identity=RuntimeExecutionIdentity(
                agent_id=interpreter.runtime_agent_id,
                session_id=interpreter.runtime_session_id,
                workspace_id=interpreter.runtime_workspace_id,
                project_id=interpreter.runtime_project_id,
            ),
            importance=0.8,
            classification=ClassificationTier.SENSITIVE,
        )
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected policy violation during episode append")

    assert "classification exceeds the active runtime policy" in message.lower()