import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_run_command_does_not_eagerly_initialize_ai_backend():
    started = time.perf_counter()
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "sona",
            "run",
            str(ROOT / "examples" / "functions.sona"),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    )
    elapsed = time.perf_counter() - started

    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "Hello, Sona developer!" in proc.stdout
    assert elapsed < 5.0


def test_interpreter_import_does_not_import_transformers():
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import sona.interpreter; print('transformers' in sys.modules)",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert proc.stdout.strip() == "False"


def test_explain_command_has_file_based_fallback_without_ai_model():
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "sona",
            "explain",
            str(ROOT / "examples" / "functions.sona"),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "It defines function(s): greet, add." in proc.stdout
    assert "Model 'qwen2.5-coder:7b' is not installed" not in proc.stdout


def test_explain_and_suggest_stay_fast_with_ollama_dotenv(tmp_path):
    (tmp_path / ".env").write_text(
        "SONA_AI_BACKEND=ollama\n"
        "SONA_OLLAMA_MODEL=qwen2.5:14b\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)

    for command in ("explain", "suggest"):
        started = time.perf_counter()
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "sona",
                command,
                str(ROOT / "examples" / "stdlib_math.sona"),
            ],
            cwd=tmp_path,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
        elapsed = time.perf_counter() - started

        assert proc.returncode == 0, proc.stderr or proc.stdout
        assert elapsed < 5.0
        assert "(local)" in proc.stdout or "local suggestions" in proc.stdout


def test_ai_backend_loads_workspace_dotenv_for_ollama(tmp_path):
    (tmp_path / ".env").write_text(
        "SONA_AI_BACKEND=ollama\n"
        "SONA_OLLAMA_MODEL=qwen2.5-coder:3b\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    env.pop("SONA_AI_BACKEND", None)
    env.pop("SONA_OLLAMA_MODEL", None)

    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from sona.ai.ai_backend import get_ai_backend; "
                "backend=get_ai_backend(); "
                "print(type(backend).__name__); "
                "print(getattr(backend, 'model', ''))"
            ),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert proc.stdout.splitlines() == ["OllamaIntegration", "qwen2.5-coder:3b"]
