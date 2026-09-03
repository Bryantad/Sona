from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from sona.proof import verify_receipt
from sona.stdlib import native_guardian as guardian

ROOT = Path(__file__).resolve().parents[2]
ONBOARDING = ROOT / "docs" / "getting-started" / "README.md"


def _sona(
    *arguments: str,
    cwd: Path,
    environment: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "sona", *arguments],
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        shell=False,
        timeout=30,
    )


def test_documented_proof_mode_onboarding_workflow(
    tmp_path: Path,
    native_binary: Path,
):
    project = tmp_path / "sona-proof-start"
    project.mkdir()
    hello = project / "hello.sona"
    denied_source = project / "denied-write.sona"
    hello.write_text('print("Proof Mode is working");\n', encoding="ascii")
    denied_source.write_text(
        'import fs; fs.write_text("blocked.txt", "must not be written");\n',
        encoding="ascii",
    )
    receipt_dir = project / ".sona" / "receipts"
    receipt_dir.mkdir(parents=True)
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    environment["SONA_NATIVE_BINARY"] = str(native_binary)

    ordinary = _sona("run", "hello.sona", cwd=project, environment=environment)
    assert ordinary.returncode == 0, ordinary.stderr or ordinary.stdout
    assert ordinary.stdout == "Proof Mode is working\n"

    hello_receipt = receipt_dir / "hello.sproof"
    generated = _sona(
        "proof",
        "hello.sona",
        "--receipt",
        str(hello_receipt),
        "--engine",
        "native",
        cwd=project,
        environment=environment,
    )
    assert generated.returncode == 0, generated.stderr or generated.stdout
    assert generated.stdout == "Proof Mode is working\n"
    assert generated.stderr == ""
    verified_hello = verify_receipt(hello_receipt)
    assert verified_hello["status"] == "valid"
    assert verified_hello["execution"]["status"] == "ok"
    assert verified_hello["engine"]["fallback_used"] is False

    inspected = _sona(
        "proof",
        "inspect",
        str(hello_receipt),
        cwd=project,
        environment=environment,
    )
    assert inspected.returncode == 0, inspected.stderr or inspected.stdout
    assert "Receipt        VALID" in inspected.stdout
    assert "Integrity      VALID" in inspected.stdout
    assert "Execution      SUCCEEDED (exit 0)" in inspected.stdout
    assert "Engine         Native Core" in inspected.stdout
    assert "Python         not involved in recorded execution" in inspected.stdout
    assert "Fallback       false" in inspected.stdout

    verified_cli = _sona(
        "proof",
        "verify",
        str(hello_receipt),
        cwd=project,
        environment=environment,
    )
    assert verified_cli.returncode == 0, verified_cli.stderr or verified_cli.stdout
    assert "Receipt        VALID" in verified_cli.stdout

    initialized = _sona(
        "guardian",
        "init",
        "--project-root",
        ".",
        "--format",
        "text",
        cwd=project,
        environment=environment,
    )
    assert initialized.returncode == 0, initialized.stderr or initialized.stdout
    assert "Sona Guardian" in initialized.stdout
    assert "State          READY" in initialized.stdout
    assert "- fs.read" in initialized.stdout and "DENY" in initialized.stdout
    assert "- fs.write" in initialized.stdout
    assert "- network" in initialized.stdout

    checked = _sona(
        "guardian",
        "check",
        "--project-root",
        ".",
        "--format",
        "text",
        cwd=project,
        environment=environment,
    )
    assert checked.returncode == 0, checked.stderr or checked.stdout
    assert "State          OK" in checked.stdout
    assert "Proof Mode     READY" in checked.stdout

    explained = _sona(
        "guardian",
        "explain",
        "--project-root",
        ".",
        "--format",
        "text",
        cwd=project,
        environment=environment,
    )
    assert explained.returncode == 0, explained.stderr or explained.stdout
    assert "State          OK" in explained.stdout
    assert "Guardian policy and baseline are valid" in explained.stdout

    config = json.loads((project / "sona.guard.json").read_text(encoding="utf-8"))
    assert config["capabilities"] == guardian.DEFAULT_CAPABILITY_POLICY
    policy = guardian.guardian_check(project)
    assert policy["status"] == "ok"
    assert policy["policy"]["policy_sha256"].startswith("sha256:")
    assert {item["decision"] for item in policy["capability_decisions"]} == {"deny"}

    denied_receipt = receipt_dir / "denied-write.sproof"
    denied = _sona(
        "proof",
        "denied-write.sona",
        "--receipt",
        str(denied_receipt),
        "--engine",
        "native",
        "--guardian-root",
        ".",
        "--allow-fs-write",
        cwd=project,
        environment=environment,
    )
    assert denied.returncode == 1
    assert "SONA-FS-005" in denied.stderr
    assert not (project / "blocked.txt").exists()

    denied_evidence = verify_receipt(denied_receipt)
    assert denied_evidence["status"] == "valid"
    assert denied_evidence["guardian_bound"] is True
    assert denied_evidence["execution"]["status"] == "failed"
    assert denied_evidence["execution"]["diagnostic"]["id"] == "SONA-FS-005"
    assert denied_evidence["capabilities"]["filesystem_write"] is False
    assert any(
        effect.get("effect") == "FS.WRITE"
        and effect["outcome"] == "denied"
        and effect.get("support") == "PARTIAL"
        for effect in denied_evidence["effects"]
    )

    denied_inspection = _sona(
        "proof",
        "inspect",
        str(denied_receipt),
        cwd=project,
        environment=environment,
    )
    assert denied_inspection.returncode == 0
    assert "Receipt        VALID" in denied_inspection.stdout
    assert "Execution      FAILED (exit 1)" in denied_inspection.stdout
    assert "Diagnostic     SONA-FS-005" in denied_inspection.stdout
    assert "- fs.write" in denied_inspection.stdout
    assert "FS.WRITE" in denied_inspection.stdout
    assert "denied (PARTIAL)" in denied_inspection.stdout

    denied_verification = _sona(
        "proof",
        "verify",
        str(denied_receipt),
        cwd=project,
        environment=environment,
    )
    assert denied_verification.returncode == 0
    assert "Receipt        VALID" in denied_verification.stdout
    assert "Execution      FAILED (exit 1)" in denied_verification.stdout

    guardian_verification = _sona(
        "guardian",
        "proof",
        "verify",
        "--project-root",
        ".",
        "--receipt",
        str(denied_receipt),
        cwd=project,
        environment=environment,
    )
    assert guardian_verification.returncode == 0
    assert json.loads(guardian_verification.stdout)["status"] == "verified"


def test_onboarding_page_has_required_commands_claims_and_valid_local_links():
    text = ONBOARDING.read_text(encoding="utf-8")
    normalized_text = " ".join(text.split())

    required_commands = [
        "python -m pip install sona-lang",
        "sona run hello.sona",
        "sona proof hello.sona",
        "sona proof inspect .sona/receipts/hello.sproof",
        "sona proof verify .sona/receipts/hello.sproof",
        "sona guardian init --project-root . --format text",
        "sona guardian check --project-root . --format text",
        "sona guardian explain --project-root . --format text",
        "--guardian-root .",
        "--allow-fs-write",
    ]
    assert all(command in text for command in required_commands)
    assert "privacy-conscious execution evidence" in normalized_text
    assert "not a digital signature" in normalized_text
    assert "remote attestation" in normalized_text
    assert "Receipt VALID` does not mean `Execution SUCCEEDED`" in (
        ROOT / "docs" / "plans" / "0.15.5-proof-mode-onboarding.md"
    ).read_text(encoding="utf-8")
    assert "Native Proof" not in text
    assert "Sona Proof" not in text

    local_links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
    assert local_links
    for target in local_links:
        if "://" in target or target.startswith("#"):
            continue
        resolved = (ONBOARDING.parent / target.split("#", 1)[0]).resolve()
        assert resolved.is_file(), f"broken onboarding link: {target}"

    assert "docs/getting-started/README.md" in (ROOT / "README.md").read_text(
        encoding="utf-8"
    )
    assert "getting-started/README.md" in (ROOT / "docs" / "README.md").read_text(
        encoding="utf-8"
    )
    assert "getting-started/README.md" in (ROOT / "docs" / "QUICKSTART.md").read_text(
        encoding="utf-8"
    )


def test_root_readme_leads_with_the_adoption_contract():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    opening = text[:9000]

    required_sections = [
        "## Why Sona?",
        "## Why not just Python?",
        "## What is Proof Mode?",
        "## What can I build today?",
        "## Try Sona quickly",
    ]
    positions = [opening.index(section) for section in required_sections]
    assert positions == sorted(positions)
    assert (
        "Sona is a simple programming language designed for software that can provide\n"
        "evidence of what it did."
    ) in opening
    assert "privacy-conscious execution evidence" in opening
    assert "Guardian" in opening and "allowed to do" in opening
    assert "not a digital signature" in opening
    assert "Native HTTP remains unavailable" in opening

    first_section = opening[: positions[0]]
    assert "Lark" not in first_section
    assert "AST" not in first_section
    assert "canonicalization" not in first_section
