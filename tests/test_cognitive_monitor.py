import pytest

from sona.interpreter import CognitiveMonitor


class StubAssistant:
    def analyze_working_memory(self, task, context):
        return {"cognitive_load": "low", "task": task, "context": context}


def test_cognitive_check_fallback_and_assistant():
    monitor = CognitiveMonitor(interpreter=None, assistant=None)
    fallback = monitor.check_cognitive_load({"task": "demo", "context": "short text"})
    assert fallback["cognitive_load"] in {"low", "medium", "high"}

    monitor_with_ai = CognitiveMonitor(interpreter=None, assistant=StubAssistant())
    assisted = monitor_with_ai.check_cognitive_load({"task": "demo", "context": "ctx"})
    assert assisted["cognitive_load"] == "low"


def test_working_memory_store_and_recall():
    monitor = CognitiveMonitor(interpreter=None, assistant=None)
    store = monitor.manage_working_memory({"action": "store", "key": "k1", "value": 42})
    assert store["status"] == "ok"
    recall = monitor.manage_working_memory({"action": "recall", "key": "k1"})
    assert recall["value"] == 42


def test_focus_mode_start_and_status():
    monitor = CognitiveMonitor(interpreter=None, assistant=None)
    start = monitor.configure_focus_mode({"task": "coding", "minutes": 15})
    assert start["status"] == "ok"
    status = monitor.configure_focus_mode({"action": "status"})
    assert status["status"] == "ok"
    assert status["active_sessions"] >= 1


def test_intent_and_decision_and_trace_toggle():
    monitor = CognitiveMonitor(interpreter=None, assistant=None)
    assert monitor.toggle_trace({"enabled": True})["trace_enabled"] is True
    intent_res = monitor.record_intent({"goal": "ship feature", "constraints": "no regressions"})
    assert intent_res["status"] == "ok"
    decision_res = monitor.record_decision({"label": "Approach A", "rationale": "Simpler"})
    assert decision_res["status"] == "ok"
    explain = monitor.explain_step({})
    assert explain["intents"]
    assert explain["decisions"]


class DummyNode:
    def __init__(self, body=None):
        self.body = body or []


def test_profile_lint_and_scope_budget():
    monitor = CognitiveMonitor(interpreter=None, assistant=None)
    assert monitor.set_profile({"profile": "adhd"})["profile"] == "adhd"

    monitor.record_intent({"goal": "cleanup"})
    lint = monitor.lint_context({"context": "delete user data"})
    assert lint["warning_count"] >= 1

    body = [DummyNode(), DummyNode([DummyNode()])]
    warnings = monitor.evaluate_scope_budget({"budget": 1}, body)
    assert warnings

    report = monitor.export_trace({})
    assert report["status"] == "ok"
