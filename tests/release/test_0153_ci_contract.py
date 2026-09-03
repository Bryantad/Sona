from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_ci_runs_external_orchestrator_for_required_matrix_and_gates() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    certifier = (ROOT / "tools/release/certify_0153.py").read_text(encoding="utf-8")
    assert "name: Sona 0.15.5 certification" in workflow
    assert "branches: [main, release/0.15.5]" in workflow
    assert "os: [ubuntu-latest, windows-latest, macos-latest]" in workflow
    assert 'python-version: ["3.11", "3.12"]' in workflow
    assert "tools/release/certify_0153.py" in workflow
    assert "--phases python,gates" in workflow
    assert "--phases native,gates" in workflow
    assert "--phases extension" in workflow
    assert "--phases packaging" in workflow
    assert "${{ runner.temp }}/sona-cert" in workflow
    assert "working-directory: vscode-extension" not in workflow
    assert 'Path("hello.sona").write_text' not in workflow
    assert 'VERSION = "0.15.3"' not in certifier
    assert 'ROOT / "pyproject.toml"' in certifier


def test_ci_has_non_skipping_native_proof_and_security_evidence() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "musl-tools file" in workflow
    assert "ilammy/msvc-dev-cmd@v1" in workflow
    assert "extension-security-evidence" in workflow
    assert "if-no-files-found: error" in workflow
    assert "continue-on-error" not in workflow
