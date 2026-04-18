import json

import pytest

from sona.runtime.memory import (
    normalize_episode_payload,
    supported_episode_kinds,
)
from sona.runtime.memory.intake import (
    RuntimeExecutionIdentity,
    RuntimeMemoryIntake,
)
from sona.runtime.memory.sqlite_store import SQLiteMemoryStore


def test_supported_episode_kinds_are_stable():
    assert supported_episode_kinds() == (
        "decision_recorded",
        "focus_transition",
        "goal_continuation_step",
        "goal_state_transition",
        "intent_recorded",
        "interpret_failure",
        "user_input",
        "working_memory_update",
    )


def test_goal_continuation_step_payload_is_canonical():
    payload = normalize_episode_payload(
        "goal_continuation_step",
        {
            "goal_title": "  Ship release  ",
            "retrieved_count": "2",
            "next_action": "  Review episode 'ep_1' for goal 'Ship release'  ",
            "action_type": "  review_memory  ",
            "reason_code": "  generic_review  ",
            "primary_memory_id": "  ep_1  ",
            "ignored": "drop-me",
        },
    )

    assert payload == {
        "goal_title": "Ship release",
        "retrieved_count": 2,
        "next_action": "Review episode 'ep_1' for goal 'Ship release'",
        "action_type": "review_memory",
        "reason_code": "generic_review",
        "primary_memory_id": "ep_1",
    }


def test_goal_state_transition_payload_is_canonical():
    payload = normalize_episode_payload(
        "goal_state_transition",
        {
            "goal_title": "  Finish release  ",
            "from_status": "  active  ",
            "to_status": "  completed  ",
            "reason": "  shipped successfully  ",
            "ignored": "drop-me",
        },
    )

    assert payload == {
        "goal_title": "Finish release",
        "from_status": "active",
        "to_status": "completed",
        "reason": "shipped successfully",
    }


def test_user_input_payload_is_canonical_and_drops_extras():
    payload = normalize_episode_payload(
        "user_input",
        {
            "filename": "  direct_input.sona  ",
            "line_count": "2",
            "text": "  print(1)  ",
            "ignored": "noise",
        },
    )

    assert payload == {
        "filename": "direct_input.sona",
        "line_count": 2,
        "text": "print(1)",
    }


def test_interpret_failure_payload_is_sorted_and_canonical():
    payload = normalize_episode_payload(
        "interpret_failure",
        {
            "message": "  boom  ",
            "filename": " fail.sona ",
            "error_type": " ZeroDivisionError ",
            "debug": "drop-me",
        },
    )

    assert list(payload.keys()) == ["error_type", "filename", "message"]
    assert payload["error_type"] == "ZeroDivisionError"
    assert payload["filename"] == "fail.sona"
    assert payload["message"] == "boom"


def test_malformed_supported_payload_raises_value_error():
    with pytest.raises(
        ValueError,
        match="missing required field 'line_count'",
    ):
        normalize_episode_payload(
            "user_input",
            {"filename": "script.sona", "text": "print(1)"},
        )


def test_generic_payload_is_sanitized_and_json_stable():
    payload = normalize_episode_payload(
        "tool_observation",
        {
            "z": None,
            "nested": {"b": 2, "a": 1},
            "tool": object(),
            "ok": True,
        },
    )

    assert list(payload.keys()) == ["nested", "ok", "tool"]
    assert payload["nested"] == {"a": 1, "b": 2}
    assert isinstance(payload["tool"], str)
    json_blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    assert json_blob.startswith('{"nested":{"a":1,"b":2},"ok":true,"tool":"')
    assert json_blob.endswith('"}')


def test_runtime_intake_persists_normalized_payload(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    intake = RuntimeMemoryIntake(store)
    identity = RuntimeExecutionIdentity(
        agent_id="sona.interpreter.test",
        session_id="sess_payloads",
        workspace_id=str(tmp_path),
        project_id="payloads",
    )

    episode = intake.append_episode(
        kind="user_input",
        source_type="runtime",
        payload={
            "filename": "  demo.sona  ",
            "line_count": "1",
            "text": "  let x = 1  ",
            "transient": "drop",
        },
        execution_identity=identity,
        attach_receipt_provenance=False,
    )

    assert episode is not None
    stored = store.query_episodes(
        agent_id="sona.interpreter.test",
        session_id="sess_payloads",
    )
    assert stored[0].payload == {
        "filename": "demo.sona",
        "line_count": 1,
        "text": "let x = 1",
    }


def test_runtime_intake_raises_for_invalid_supported_payload(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    intake = RuntimeMemoryIntake(store)
    identity = RuntimeExecutionIdentity(
        agent_id="sona.interpreter.test",
        session_id="sess_invalid",
    )

    with pytest.raises(ValueError):
        intake.append_episode(
            kind="user_input",
            source_type="runtime",
            payload={"filename": "demo.sona", "text": "let x = 1"},
            execution_identity=identity,
            attach_receipt_provenance=False,
        )
