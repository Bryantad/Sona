import json

from sona.developer_intelligence import TaskRequest, TaskResult, TaskStatus, TaskType
from sona.developer_intelligence.config import reload_config, resolve_config, resolve_credential
from sona.developer_intelligence.receipts import build_task_receipt


def test_configuration_precedence(tmp_path, monkeypatch):
    monkeypatch.setenv("SONA_AI_PROVIDER", "environment")
    (tmp_path / ".env").write_text("SONA_AI_PROVIDER=dotenv\n", encoding="utf-8")
    (tmp_path / "sona.config.json").write_text(json.dumps({"providers": {"selected": "legacy"}}), encoding="utf-8")
    (tmp_path / ".sona").mkdir()
    (tmp_path / ".sona" / "config.json").write_text(json.dumps({"providers": {"selected": "workspace"}}), encoding="utf-8")
    reload_config()
    assert resolve_config(tmp_path)["providers"]["selected"] == "workspace"
    assert resolve_config(tmp_path, {"providers": {"selected": "request"}})["providers"]["selected"] == "request"


def test_absent_higher_layers_do_not_erase_user_or_environment_values(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    (home / "config.json").write_text('{"providers":{"selected":"user"}}', encoding="utf-8")
    monkeypatch.setenv("SONA_HOME", str(home))
    monkeypatch.setenv("SONA_AI_PROVIDER", "environment")
    reload_config()
    assert resolve_config(tmp_path)["providers"]["selected"] == "user"
    (home / "config.json").write_text('{}', encoding="utf-8")
    reload_config()
    assert resolve_config(tmp_path)["providers"]["selected"] == "environment"
    reload_config()


def test_plaintext_credentials_are_ignored_in_every_json_layer(tmp_path, monkeypatch):
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    (workspace / ".sona").mkdir(parents=True)
    home.mkdir()
    (home / "config.json").write_text('{"api_key":"user-secret"}', encoding="utf-8")
    (workspace / "sona.config.json").write_text('{"providers":{"token":"legacy-secret"}}', encoding="utf-8")
    (workspace / ".sona" / "config.json").write_text('{"providers":{"password":"workspace-secret"}}', encoding="utf-8")
    monkeypatch.setenv("SONA_HOME", str(home))
    reload_config()
    resolved = resolve_config(workspace)
    rendered = str(resolved)
    assert "user-secret" not in rendered
    assert "legacy-secret" not in rendered
    assert "workspace-secret" not in rendered
    assert resolved["credential_migration_warning"]
    reload_config()


def test_workspace_dotenv_credentials_override_process_without_entering_config(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("AZURE_OPENAI_API_KEY=workspace-secret\n", encoding="utf-8")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "process-secret")
    reload_config()
    assert resolve_credential(tmp_path, "AZURE_OPENAI_API_KEY") == "workspace-secret"
    assert "workspace-secret" not in str(resolve_config(tmp_path))
    reload_config()


def test_receipt_redaction_hashing_and_determinism():
    request = TaskRequest(TaskType.EXPLAIN, "api_key=super-secret", task_id="fixed")
    result = TaskResult("fixed", TaskType.EXPLAIN, TaskStatus.OK, "token=also-secret")
    first = build_task_receipt(request, result, policy_hash="abc", started_at="2026-01-01T00:00:00Z")
    second = build_task_receipt(request, result, policy_hash="abc", started_at="2026-01-01T00:00:00Z")
    assert first == second
    text = json.dumps(first)
    assert "super-secret" not in text
    assert "also-secret" not in text
    assert first["receipt_hash"].startswith("sha256:")
