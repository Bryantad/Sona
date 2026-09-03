from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / "examples" / "trusted-workflows"


def _python() -> str:
    return sys.executable


def _sona(*arguments: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    return subprocess.run(
        [_python(), "-m", "sona", *arguments],
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.parametrize(
    ("relative_path", "expected"),
    [
        ("ai-action-receipt/workflow.sona", "Controlled proposal action completed."),
        ("auditable-calculation/invoice.sona", "Total cents: 12875"),
        ("deployment-evidence/deploy.sona", "Environment label: local-staging"),
    ],
)
def test_native_workflow_sources_execute_with_expected_output(
    tmp_path, relative_path, expected
):
    source = WORKFLOWS / relative_path
    directory = tmp_path / source.parent.name
    shutil.copytree(source.parent, directory)
    copied_source = directory / source.name
    checked = _sona("check", str(copied_source), cwd=directory)
    executed = _sona(
        "run",
        copied_source.name,
        "--compatibility",
        "sona",
        cwd=directory,
    )

    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert executed.returncode == 0, executed.stdout + executed.stderr
    assert expected in executed.stdout


def test_deployment_artifact_digest_matches_declared_metadata():
    directory = WORKFLOWS / "deployment-evidence"
    artifact = directory / "artifact" / "app.txt"
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    source = (directory / "deploy.sona").read_text(encoding="utf-8")

    assert digest == "9d9d72726b51c85cb293b2383e180f4f39c12dbbe66d41acab811d5a45687de8"
    assert digest in source


def test_service_api_example_uses_real_loopback_compatibility_runtime():
    directory = WORKFLOWS / "service-api"
    server = subprocess.Popen(
        [_python(), "fixture_server.py"],
        cwd=directory,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        assert server.stdout is not None
        deadline = time.monotonic() + 5
        line = ""
        while time.monotonic() < deadline and not line:
            line = server.stdout.readline().strip()
        assert "127.0.0.1:8765" in line

        result = _sona(
            "run",
            "client.sona",
            "--compatibility",
            "sona",
            cwd=directory,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "Service status: 200" in result.stdout
        payload_line = next(
            line for line in result.stdout.splitlines() if '"service"' in line
        )
        assert json.loads(payload_line) == {
            "service": "sona-example",
            "status": "ok",
        }
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)


def test_workflow_docs_state_current_trust_boundaries():
    ai = (WORKFLOWS / "ai-action-receipt" / "README.md").read_text(encoding="utf-8")
    service = (WORKFLOWS / "service-api" / "README.md").read_text(encoding="utf-8")
    deploy = (WORKFLOWS / "deployment-evidence" / "README.md").read_text(
        encoding="utf-8"
    )

    assert "does **not** invoke a model" in ai
    assert "does\n**not** produce a Native Proof Mode receipt" in service
    assert "Declared metadata" in deploy
    assert "not authenticated host identity" in deploy


def test_deploy_command_is_deferred_until_contracts_exist():
    design = (ROOT / "docs" / "plans" / "0.15.5-deployment-contract.md").read_text(
        encoding="utf-8"
    )
    cli = (ROOT / "sona" / "cli.py").read_text(encoding="utf-8")

    assert "will not add `sona deploy`" in design
    assert "authenticated environment or host identity" in design
    assert "deployment rollback protocol" in design
    assert "add_parser('deploy'" not in cli
    assert 'add_parser("deploy"' not in cli
