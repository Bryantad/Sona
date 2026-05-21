import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _run_sona_file(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "sona", "run", str(path)],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        timeout=180,
    )


def test_undefined_variable_has_stable_error_shape(tmp_path):
    source = tmp_path / "undefined.sona"
    source.write_text("print(total);\n", encoding="utf-8")

    result = _run_sona_file(source)

    assert result.returncode == 1
    assert "SonaNameError:" in result.stderr
    assert "hint:" in result.stderr
    assert "Traceback" not in result.stderr


def test_syntax_error_has_stable_error_shape(tmp_path):
    source = tmp_path / "syntax.sona"
    source.write_text('print("missing close);\n', encoding="utf-8")

    result = _run_sona_file(source)

    assert result.returncode == 1
    assert "SonaSyntaxError:" in result.stderr
    assert "hint:" in result.stderr
    assert "Traceback" not in result.stderr


def test_import_typo_has_stdlib_suggestion(tmp_path):
    source = tmp_path / "import_typo.sona"
    source.write_text("import mathh;\n", encoding="utf-8")

    result = _run_sona_file(source)

    assert result.returncode == 1
    assert "SonaImportError: module 'mathh' not found" in result.stderr
    assert "hint: did you mean 'math'?" in result.stderr
    assert "[INFO]" not in result.stdout + result.stderr
    assert "DEBUG" not in result.stdout + result.stderr
    assert "Traceback" not in result.stderr
