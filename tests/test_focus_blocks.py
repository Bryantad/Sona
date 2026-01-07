from sona.interpreter import SonaInterpreter


def test_nested_focus_restores_state():
    interpreter = SonaInterpreter()
    monitor = interpreter.cognitive_monitor
    monitor.trace_enabled = False

    code = """
    focus {
        focus {
            let x = 1;
        }
    }
    """

    interpreter.interpret(code, filename="<focus-nested>")

    assert interpreter.focus_block_active is False
    assert interpreter.focus_block_stack == []
    assert interpreter.suppress_diagnostics is False
    assert interpreter.auto_ai_suggestions_enabled is True
    assert monitor.trace_enabled is False
    assert monitor.scope_stack == []


def test_intent_annotation_records_for_block_and_statement():
    interpreter = SonaInterpreter()
    monitor = interpreter.cognitive_monitor

    code = """
    @intent "block intent"
    focus { let x = 1; }
    @intent "statement intent"
    let y = 2;
    """

    interpreter.interpret(code, filename="<intent-annotations>")

    intents = monitor.intent_stack[-2:]
    assert [intent["goal"] for intent in intents] == ["block intent", "statement intent"]
    assert all(intent["meta"].get("annotation") is True for intent in intents)
