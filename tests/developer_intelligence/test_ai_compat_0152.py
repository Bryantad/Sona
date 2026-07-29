import sys


def test_sona_ai_public_entrypoint_is_lazy_developer_adapter(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    heavy = {"torch", "transformers", "accelerate", "openai", "anthropic"}
    before = heavy & set(sys.modules)
    import sona.ai as legacy

    backend = legacy.get_ai_backend()
    assert type(backend).__name__ == "DeveloperIntelligenceCompatibilityAdapter"
    assert (heavy & set(sys.modules)) == before
    result = backend.run_task("explain", "Explain developer code.", context="let answer = 42;")
    assert result.task_type.value == "explain"
    assert result.receipt_path


def test_sona_ai_adapter_rejects_general_chat_task_type():
    import sona.ai as legacy
    try:
        legacy.get_ai_backend().run_task("chat", "hello")
    except ValueError as exc:
        assert "chat" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("general chat must not be accepted")
