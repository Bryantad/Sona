from __future__ import annotations

import json
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from sona.stdlib import native_guardian as guardian


ROOT = Path(__file__).resolve().parents[2]
CURRENT_VERSION = "0.15.4"


@pytest.fixture(scope="module")
def native_binary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    cargo = shutil.which("cargo")
    assert cargo is not None, "cargo is mandatory for the active native gates"
    target = tmp_path_factory.mktemp("native-target")
    environment = os.environ.copy()
    environment["CARGO_TARGET_DIR"] = str(target)
    process = subprocess.run(
        [
            cargo,
            "build",
            "--manifest-path",
            str(ROOT / "native" / "Cargo.toml"),
            "--release",
            "--locked",
            "-p",
            "sona-cli",
        ],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        shell=False,
        timeout=180,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    binary = target / "release" / ("sona.exe" if os.name == "nt" else "sona")
    assert binary.is_file()
    return binary


def test_native_standalone_gate_passes(tmp_path: Path, native_binary: Path):
    process = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tests" / "release" / "run_0153_native_standalone_gate.py"),
            "--native-binary",
            str(native_binary),
            "--output-dir",
            str(tmp_path),
            "--sona-version",
            CURRENT_VERSION,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        shell=False,
        timeout=120,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    summary = json.loads(
        (tmp_path / f"sona-{CURRENT_VERSION}-native-standalone.json").read_text(
            encoding="utf-8"
        )
    )
    assert summary["schema_id"] == "sona.native-standalone.schema-1"
    assert summary["python_removed_from_child_path"] is True
    assert summary["result_counters"]["fail"] == 0


def test_differential_conformance_has_exact_accounting(
    tmp_path: Path, native_binary: Path
):
    process = subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "tests"
                / "conformance"
                / "run_0153_differential_conformance.py"
            ),
            "--native-binary",
            str(native_binary),
            "--output-dir",
            str(tmp_path),
            "--sona-version",
            CURRENT_VERSION,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        shell=False,
        timeout=180,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    summary = json.loads(
        (tmp_path / f"sona-{CURRENT_VERSION}-differential-conformance.json").read_text(
            encoding="utf-8"
        )
    )
    assert summary["schema_id"] == "sona.differential-conformance.schema-1"
    assert summary["fixtures"] == 20
    assert summary["engine_executions"] == 40
    assert summary["comparisons"] == 20
    assert summary["comparison_pass"] == 20
    assert summary["comparison_fail"] == 0
    assert summary["scope"] == "bounded cross-engine conformance"


def _native_run(
    native_binary: Path,
    *args: str,
    cwd: Path,
    input_data: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [str(native_binary), *args],
        cwd=cwd,
        capture_output=True,
        input=input_data,
        shell=False,
        timeout=30,
    )


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _write_source(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def test_native_proof_receipt_is_redacted_canonical_and_matches_run_output(
    tmp_path: Path, native_binary: Path
):
    source = tmp_path / "proof.sona"
    source.write_bytes(b'import io; io.write_stdout("value"); io.write_stderr("warn"); print("line");\r\n')
    normal = _native_run(native_binary, "run", str(source), "--engine", "native", cwd=tmp_path)
    receipt_path = tmp_path / "proof.json"
    proof = _native_run(
        native_binary,
        "proof",
        str(source),
        "--receipt",
        str(receipt_path),
        "--engine",
        "native",
        cwd=tmp_path,
    )

    assert proof.returncode == normal.returncode == 0
    assert proof.stdout == normal.stdout == b"valueline\n"
    assert proof.stderr == normal.stderr == b"warn"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["schema_id"] == "sona.native-proof.schema-1"
    assert receipt["engine"] == {
        "fallback_used": False,
        "name": "native",
        "python_embedded": False,
        "python_required": False,
    }
    assert receipt["program"] == {
        "kind": "source",
        "source": {"sha256": _sha256(source.read_bytes()), "bytes": len(source.read_bytes())},
    }
    assert receipt["execution"]["stdout"] == {
        "sha256": _sha256(proof.stdout),
        "bytes": len(proof.stdout),
    }
    assert receipt["execution"]["stderr"] == {
        "sha256": _sha256(proof.stderr),
        "bytes": len(proof.stderr),
    }
    unsigned = dict(receipt)
    receipt_hash = unsigned.pop("receipt_hash")
    canonical = json.dumps(unsigned, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    assert receipt_hash == _sha256(canonical)
    assert receipt_hash != _sha256(canonical + b"\n")
    rendered = receipt_path.read_text(encoding="utf-8")
    assert str(source) not in rendered
    assert "value" not in rendered
    assert "warn" not in rendered


def test_native_proof_summary_is_opt_in_and_excluded_from_receipt_output_hashes(
    tmp_path: Path, native_binary: Path
):
    source = tmp_path / "summary.sona"
    _write_source(source, 'print("operator view");\n')
    receipt_path = tmp_path / "summary-proof.json"
    proof = _native_run(
        native_binary,
        "proof",
        str(source),
        "--receipt",
        str(receipt_path),
        "--summary",
        cwd=tmp_path,
    )

    assert proof.returncode == 0
    assert proof.stdout == b"operator view\n"
    summary = proof.stderr.decode("utf-8", "replace")
    assert "Proof receipt saved" in summary
    assert "  Execution     succeeded" in summary
    assert "  Engine        Native Core" in summary
    assert f"  Receipt       {receipt_path}" in summary
    assert "  Evidence      1 observed effect" in summary
    assert "  Output        14 B stdout, 0 B stderr" in summary
    assert "  Duration      " in summary

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["execution"]["stdout"] == {
        "sha256": _sha256(proof.stdout),
        "bytes": len(proof.stdout),
    }
    assert receipt["execution"]["stderr"] == {
        "sha256": _sha256(b""),
        "bytes": 0,
    }
    assert receipt["receipt_hash"] in summary

    failed_source = tmp_path / "summary-failure.sona"
    _write_source(failed_source, "fn legacy() { return 1; };\n")
    failed_receipt = tmp_path / "summary-failure.json"
    failed = _native_run(
        native_binary,
        "proof",
        str(failed_source),
        "--receipt",
        str(failed_receipt),
        "--summary",
        cwd=tmp_path,
    )
    assert failed.returncode == 1
    assert b"Proof receipt saved" not in failed.stderr
    assert failed_receipt.is_file()


def test_native_proof_binds_to_guardian_and_can_be_attested(
    tmp_path: Path, native_binary: Path
):
    project = tmp_path / "guardian-project"
    project.mkdir()
    source = project / "app.sona"
    _write_source(source, 'print("guardian-bound");\n')
    initialized = guardian.guardian_init(project)
    receipt_dir = project / ".sona" / "receipts"
    receipt_dir.mkdir(parents=True)
    receipt_path = receipt_dir / "guardian-proof.json"

    proof = _native_run(
        native_binary,
        "proof",
        str(source),
        "--receipt",
        str(receipt_path),
        "--guardian-root",
        str(project),
        "--summary",
        cwd=project,
    )
    assert proof.returncode == 0, proof.stderr.decode("utf-8", "replace")
    assert proof.stdout == b"guardian-bound\n"
    summary = proof.stderr.decode("utf-8", "replace")
    assert f"  Guardian      Bound baseline {initialized['snapshot_id']}" in summary

    rendered = receipt_path.read_text(encoding="utf-8")
    receipt = json.loads(rendered)
    assert receipt["guardian"] == {
        "schema_id": "sona.guardian-proof-binding.schema-1",
        "baseline_snapshot_id": initialized["snapshot_id"],
        "baseline_sha256": _sha256((project / ".sona" / "guardian" / "baseline.json").read_bytes()),
        "trusted_config_sha256": _sha256((project / ".sona" / "guardian" / "trusted_config.json").read_bytes()),
        "program_baseline": "tracked",
    }
    assert str(project) not in rendered
    assert "app.sona" not in rendered

    verified = guardian.guardian_proof_verify(project, receipt_path)
    assert verified["status"] == "verified"
    assert guardian.guardian_proof_attest(project, receipt_path)["status"] == "attested"
    reviewed = guardian.guardian_proof_review(project, receipt_path, "deterministic")
    assert reviewed["status"] == "reviewed"
    assert reviewed["evidence"]["local_attestation_recorded"] is True
    assert reviewed["reviewer"]["advisory"] is True
    assert str(project) not in json.dumps(reviewed)
    assert str(receipt_path) not in json.dumps(reviewed)
    assert guardian.guardian_proof_history(project)[0]["payload"]["receipt_hash"] == receipt["receipt_hash"]

    source.write_text('print("changed after baseline");\n', encoding="utf-8")
    stale_receipt = receipt_dir / "stale-guardian-proof.json"
    stale = _native_run(
        native_binary,
        "proof",
        str(source),
        "--receipt",
        str(stale_receipt),
        "--guardian-root",
        str(project),
        cwd=project,
    )
    assert stale.returncode == 1
    assert stale.stdout == b""
    assert b"PROOF-008" in stale.stderr
    assert not stale_receipt.exists()


def test_native_proof_sbc_preserves_container_and_exact_source_identity(
    tmp_path: Path, native_binary: Path
):
    source = tmp_path / "source.sona"
    source.write_bytes(b'print("container");\r\n')
    container = tmp_path / "source.sbc"
    compiled = _native_run(
        native_binary, "compile", str(source), "--output", str(container), cwd=tmp_path
    )
    assert compiled.returncode == 0, compiled.stderr.decode("utf-8", "replace")

    receipt_path = tmp_path / "container-proof.json"
    proof = _native_run(
        native_binary,
        "proof",
        str(container),
        "--receipt",
        str(receipt_path),
        cwd=tmp_path,
    )
    assert proof.returncode == 0, proof.stderr.decode("utf-8", "replace")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["program"] == {
        "kind": "sbc",
        "container": {"sha256": _sha256(container.read_bytes()), "bytes": len(container.read_bytes())},
        "source": {"sha256": _sha256(source.read_bytes()), "bytes": len(source.read_bytes())},
    }


def test_native_proof_preserves_program_diagnostic_ownership_and_receipt(
    tmp_path: Path, native_binary: Path
):
    source = tmp_path / "legacy.sona"
    _write_source(source, "fn legacy() { return 1; };\n")
    receipt_path = tmp_path / "legacy-proof.json"
    process = _native_run(
        native_binary, "proof", str(source), "--receipt", str(receipt_path), cwd=tmp_path
    )
    normal = _native_run(native_binary, "run", str(source), "--engine", "native", cwd=tmp_path)
    assert process.returncode == 1
    assert process.stdout == normal.stdout
    assert process.stderr == normal.stderr
    assert b"SONA-PARSE-001" in process.stderr
    assert b"PROOF-" not in process.stderr
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["execution"]["status"] == "failed"
    assert receipt["execution"]["diagnostic"]["id"] == "SONA-PARSE-001"

    denied = tmp_path / "denied.sona"
    _write_source(denied, 'import fs; print(fs.read_text("secret.txt"));\n')
    denied_receipt = tmp_path / "denied-proof.json"
    process = _native_run(
        native_binary, "proof", str(denied), "--receipt", str(denied_receipt), cwd=tmp_path
    )
    normal = _native_run(native_binary, "run", str(denied), "--engine", "native", cwd=tmp_path)
    assert process.returncode == 1
    assert process.stdout == normal.stdout
    assert process.stderr == normal.stderr
    assert b"SONA-FS-005" in process.stderr
    assert b"PROOF-" not in process.stderr
    receipt = json.loads(denied_receipt.read_text(encoding="utf-8"))
    assert receipt["execution"]["diagnostic"]["id"] == "SONA-FS-005"
    assert receipt["effects"][0]["outcome"] == "denied"


def test_native_proof_uses_private_per_execution_target_fingerprints(
    tmp_path: Path, native_binary: Path
):
    target = tmp_path / "sensitive-target.txt"
    target.write_text("present", encoding="utf-8")
    source = tmp_path / "effects.sona"
    _write_source(
        source,
        'import fs; print(fs.exists("sensitive-target.txt")); print(fs.exists("sensitive-target.txt"));\n',
    )

    first_receipt = tmp_path / "first.json"
    first = _native_run(
        native_binary,
        "proof",
        str(source),
        "--receipt",
        str(first_receipt),
        "--allow-fs-read",
        cwd=tmp_path,
    )
    assert first.returncode == 0, first.stderr.decode("utf-8", "replace")
    first_payload = json.loads(first_receipt.read_text(encoding="utf-8"))
    filesystem = [item for item in first_payload["effects"] if item["scope"] == "filesystem"]
    assert len(filesystem) == 2
    assert filesystem[0]["target"].startswith("hmac-sha256:")
    assert filesystem[0]["target"] == filesystem[1]["target"]
    assert "sensitive-target" not in first_receipt.read_text(encoding="utf-8")

    second_receipt = tmp_path / "second.json"
    second = _native_run(
        native_binary,
        "proof",
        str(source),
        "--receipt",
        str(second_receipt),
        "--allow-fs-read",
        cwd=tmp_path,
    )
    assert second.returncode == 0
    second_payload = json.loads(second_receipt.read_text(encoding="utf-8"))
    second_target = next(item["target"] for item in second_payload["effects"] if item["scope"] == "filesystem")
    assert second_target != filesystem[0]["target"]


def test_native_proof_never_records_stdin_values_or_fingerprints(
    tmp_path: Path, native_binary: Path
):
    source = tmp_path / "stdin.sona"
    _write_source(source, "import stdin; print(stdin.read());\n")
    receipt_path = tmp_path / "stdin-proof.json"
    process = _native_run(
        native_binary,
        "proof",
        str(source),
        "--receipt",
        str(receipt_path),
        cwd=tmp_path,
        input_data=b"0420\n",
    )
    assert process.returncode == 0
    assert process.stdout == b"0420\n"
    receipt_text = receipt_path.read_text(encoding="utf-8")
    receipt = json.loads(receipt_text)
    stdin_effect = next(item for item in receipt["effects"] if item["scope"] == "stdin")
    assert stdin_effect == {
        "operation": "read",
        "outcome": "allowed",
        "scope": "stdin",
        "sequence": 1,
    }
    assert "0420" not in receipt_text


def test_native_proof_infrastructure_and_container_failures_have_exact_owners(
    tmp_path: Path, native_binary: Path
):
    source = tmp_path / "source.sona"
    _write_source(source, 'print("ok");\n')
    existing = tmp_path / "existing.json"
    existing.write_text("{}\n", encoding="utf-8")

    cases = [
        (["proof", str(source)], "PROOF-001"),
        (["proof", str(tmp_path / "unsupported.txt"), "--receipt", str(tmp_path / "x.json")], "PROOF-002"),
        (["proof", str(source), "--receipt", str(tmp_path / "missing" / "x.json")], "PROOF-003"),
        (["proof", str(source), "--receipt", str(existing)], "PROOF-004"),
        (["proof", str(source), "--receipt", str(tmp_path / "engine.json"), "--engine", "python-compat"], "SONA-NATIVE-CLI-004"),
    ]
    for arguments, diagnostic_id in cases:
        process = _native_run(native_binary, *arguments, cwd=tmp_path)
        assert process.returncode == 1
        assert diagnostic_id.encode("utf-8") in process.stderr
        if diagnostic_id != "PROOF-001":
            assert b"PROOF-001" not in process.stderr

    malformed = tmp_path / "malformed.sbc"
    malformed.write_bytes(b"not-an-sbc")
    malformed_receipt = tmp_path / "malformed.json"
    process = _native_run(
        native_binary, "proof", str(malformed), "--receipt", str(malformed_receipt), cwd=tmp_path
    )
    assert process.returncode == 1
    assert b"SONA-NATIVE-BYTECODE-001" in process.stderr
    assert b"PROOF-" not in process.stderr
    assert not malformed_receipt.exists()

    run = _native_run(native_binary, "run", str(source), "--engine", "native", cwd=tmp_path)
    assert run.returncode == 0
    assert b"PROOF-" not in run.stdout + run.stderr
    container = tmp_path / "normal.sbc"
    compiled = _native_run(
        native_binary, "compile", str(source), "--output", str(container), cwd=tmp_path
    )
    assert compiled.returncode == 0
    executed = _native_run(native_binary, "exec", str(container), cwd=tmp_path)
    assert executed.returncode == 0
    assert b"PROOF-" not in executed.stdout + executed.stderr
