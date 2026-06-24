import json
import os
import subprocess
import sys
from pathlib import Path

import sona.setup_azure as setup_azure


ROOT = Path(__file__).resolve().parents[2]


def test_setup_manual_writes_config_and_workspace_env(tmp_path):
    workspace = tmp_path / "workspace"
    sona_home = tmp_path / "sona-home"
    env = os.environ.copy()
    env["SONA_HOME"] = str(sona_home)
    env["PYTHONPATH"] = str(ROOT)

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "sona",
            "setup",
            "manual",
            "--workspace",
            str(workspace),
        ],
        cwd=ROOT,
        env=env,
        input="https://example.openai.azure.com/\nsecret-key\nchat-prod\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "Failed to load setup" not in proc.stdout
    assert "[OK] Manual Azure setup complete." in proc.stdout

    config = json.loads((sona_home / "config.json").read_text(encoding="utf-8"))
    assert config == {
        "endpoint": "https://example.openai.azure.com/",
        "api_key": "secret-key",
        "deployment": "chat-prod",
    }

    env_file = (workspace / ".env").read_text(encoding="utf-8")
    assert "AZURE_OPENAI_ENDPOINT=https://example.openai.azure.com/" in env_file
    assert "AZURE_OPENAI_API_KEY=secret-key" in env_file
    assert "AZURE_OPENAI_DEPLOYMENT=chat-prod" in env_file
    assert "AZURE_OPENAI_DEPLOYMENT_NAME=chat-prod" in env_file
    assert "SONA_AI_PROVIDER=azure" in env_file


def test_update_env_file_preserves_existing_content(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    env_path = workspace / ".env"
    env_path.write_text(
        "# existing config\n"
        "APP_MODE=dev\n"
        "SONA_AI_PROVIDER=openai\n"
        "AZURE_OPENAI_ENDPOINT=old\n",
        encoding="utf-8",
    )

    setup_azure._update_env_file(workspace, "https://new.example/", "key", "deploy")

    content = env_path.read_text(encoding="utf-8")
    assert "# existing config" in content
    assert "APP_MODE=dev" in content
    assert "SONA_AI_PROVIDER=openai" in content
    assert "AZURE_OPENAI_ENDPOINT=https://new.example/" in content
    assert "AZURE_OPENAI_API_KEY=key" in content
    assert "AZURE_OPENAI_DEPLOYMENT=deploy" in content


def test_setup_manual_local_writes_ollama_config(monkeypatch, tmp_path, capsys):
    workspace = tmp_path / "workspace"
    sona_home = tmp_path / "sona-home"
    answers = iter(["local", ""])

    def fake_status(model=None):
        selected = model or setup_azure.DEFAULT_LOCAL_MODEL
        return {
            "status": "ready",
            "model": selected,
            "ollama_host": "http://localhost:11434",
            "ollama_running": True,
            "installed": True,
            "models": ["qwen2.5-coder:7b"],
        }

    monkeypatch.setenv("SONA_HOME", str(sona_home))
    monkeypatch.setattr(setup_azure, "_input", lambda _prompt: next(answers))
    monkeypatch.setattr(setup_azure, "_local_model_status", fake_status)

    assert setup_azure._manual_setup(False, workspace) == 0
    output = capsys.readouterr().out
    assert "[OK] Manual local AI setup complete." in output

    config = json.loads((sona_home / "config.json").read_text(encoding="utf-8"))
    assert config == {
        "provider": "ollama",
        "backend": "ollama",
        "model": "qwen2.5-coder:7b",
        "ollama_host": "http://localhost:11434",
    }

    env_file = (workspace / ".env").read_text(encoding="utf-8")
    assert "SONA_AI_PROVIDER=ollama" in env_file
    assert "SONA_AI_BACKEND=ollama" in env_file
    assert "SONA_OLLAMA_MODEL=qwen2.5-coder:7b" in env_file
    assert "OLLAMA_HOST=http://localhost:11434" in env_file


def test_setup_manual_local_detects_general_qwen_model(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    sona_home = tmp_path / "sona-home"
    answers = iter(["local", ""])

    def fake_status(model=None):
        selected = model or setup_azure.DEFAULT_LOCAL_MODEL
        return {
            "status": "missing" if selected == setup_azure.DEFAULT_LOCAL_MODEL else "ready",
            "model": selected,
            "ollama_host": "http://localhost:11434",
            "ollama_running": True,
            "installed": selected == "qwen2.5:14b",
            "models": ["llama3:latest", "qwen2.5vl:3b", "qwen2.5:14b"],
        }

    monkeypatch.setenv("SONA_HOME", str(sona_home))
    monkeypatch.setattr(setup_azure, "_input", lambda _prompt: next(answers))
    monkeypatch.setattr(setup_azure, "_local_model_status", fake_status)

    assert setup_azure._manual_setup(False, workspace) == 0

    env_file = (workspace / ".env").read_text(encoding="utf-8")
    assert "SONA_OLLAMA_MODEL=qwen2.5:14b" in env_file


def test_setup_manual_local_missing_model_does_not_write(monkeypatch, tmp_path, capsys):
    workspace = tmp_path / "workspace"
    sona_home = tmp_path / "sona-home"
    answers = iter(["local", "qwen3-coder:30b"])

    def fake_status(model=None):
        return {
            "status": "missing",
            "model": model or setup_azure.DEFAULT_LOCAL_MODEL,
            "ollama_host": "http://localhost:11434",
            "ollama_running": True,
            "installed": False,
            "models": [],
        }

    monkeypatch.setenv("SONA_HOME", str(sona_home))
    monkeypatch.setattr(setup_azure, "_input", lambda _prompt: next(answers))
    monkeypatch.setattr(setup_azure, "_local_model_status", fake_status)

    assert setup_azure._manual_setup(False, workspace) == 1
    output = capsys.readouterr().out
    assert "Model 'qwen3-coder:30b' is not installed" in output
    assert "sona ai-model pull --model qwen3-coder:30b" in output
    assert not (workspace / ".env").exists()
    assert not (sona_home / "config.json").exists()


def test_azure_setup_missing_cli_returns_actionable_code(monkeypatch, capsys):
    def fail_run(_cmd):
        raise FileNotFoundError("az")

    monkeypatch.setattr(setup_azure, "_run", fail_run)

    assert setup_azure.setup_azure() == 2
    output = capsys.readouterr().out
    assert "Azure CLI not found" in output
    assert "sona setup manual" in output


def test_setup_manual_without_stdin_fails_cleanly(tmp_path):
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "sona",
            "setup",
            "manual",
            "--workspace",
            str(tmp_path),
        ],
        cwd=ROOT,
        input="",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=5,
    )

    assert proc.returncode == 1
    assert "[ERROR] Endpoint is required." in proc.stdout
    assert "Traceback" not in proc.stderr
