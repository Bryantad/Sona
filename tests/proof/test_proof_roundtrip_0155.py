from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from sona.proof import ProofDiagnostic, canonical_json_bytes, verify_receipt
from sona.stdlib import native_guardian as guardian

ROOT = Path(__file__).resolve().parents[2]
COMPAT_RECEIPT = ROOT / "tests" / "proof" / "fixtures" / "0.15.4-native-hello.json"


def _native_run(
    native_binary: Path,
    *args: str,
    cwd: Path,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [str(native_binary), *args],
        cwd=cwd,
        capture_output=True,
        check=False,
        shell=False,
        timeout=30,
    )


def _python_verify(receipt: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        str(ROOT)
        if not existing_pythonpath
        else str(ROOT) + os.pathsep + existing_pythonpath
    )
    return subprocess.run(
        [sys.executable, "-m", "sona", "proof", "verify", str(receipt)],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        shell=False,
        timeout=30,
    )


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _assert_native_engine(result: dict, *, extended: bool = True) -> None:
    expected = {
        "name": "native",
        "label": "Native Core",
        "python_required": False,
        "python_embedded": False,
        "fallback_used": False,
    }
    for key, value in expected.items():
        assert result["engine"][key] == value
    if extended:
        runtime_identity = result["engine"]["runtime_identity"]
        assert runtime_identity["native_binary"]["bytes"] > 0
        assert runtime_identity["native_binary"]["sha256"].startswith("sha256:")
        assert runtime_identity["source_revision"] == "git:" + "1" * 40
    else:
        assert "runtime_identity" not in result["engine"]


def test_real_native_source_round_trip_and_run_behavior_match(
    tmp_path: Path,
    native_binary: Path,
):
    data = tmp_path / "input.txt"
    data.write_bytes(b"trusted input")
    source = tmp_path / "roundtrip.sona"
    source.write_bytes(
        b'import fs; import io; io.write_stdout(fs.read_text("input.txt")); '
        b'io.write_stderr("warn");\r\n'
    )

    normal = _native_run(
        native_binary,
        "run",
        str(source),
        "--engine",
        "native",
        "--allow-fs-read",
        cwd=tmp_path,
    )
    receipt_path = tmp_path / "source-proof.json"
    proof = _native_run(
        native_binary,
        "proof",
        str(source),
        "--receipt",
        str(receipt_path),
        "--engine",
        "native",
        "--allow-fs-read",
        cwd=tmp_path,
    )

    assert proof.returncode == normal.returncode == 0
    assert proof.stdout == normal.stdout == b"trusted input"
    assert proof.stderr == normal.stderr == b"warn"

    result = verify_receipt(receipt_path)
    _assert_native_engine(result)
    assert result["engine"]["runtime_identity"]["native_binary"] == {
        "sha256": _sha256(native_binary.read_bytes()),
        "bytes": native_binary.stat().st_size,
    }
    assert result["status"] == "valid"
    assert result["program"] == {
        "kind": "source",
        "source": {"sha256": _sha256(source.read_bytes()), "bytes": len(source.read_bytes())},
    }
    assert result["capabilities"]["filesystem_read"] is True
    assert result["capabilities"]["filesystem_write"] is False
    assert result["execution"]["status"] == "ok"
    assert result["execution"]["stdout"] == {
        "sha256": _sha256(proof.stdout),
        "bytes": len(proof.stdout),
    }
    assert result["execution"]["stderr"] == {
        "sha256": _sha256(proof.stderr),
        "bytes": len(proof.stderr),
    }
    assert any(
        effect["scope"] == "filesystem"
        and effect["operation"] == "fs.read_text"
        and effect["effect"] == "FS.READ"
        and effect["support"] == "SUPPORTED"
        and effect["outcome"] == "allowed"
        for effect in result["effects"]
    )

    cli = _python_verify(receipt_path)
    assert cli.returncode == 0, cli.stderr or cli.stdout
    assert "Proof Mode Verification" in cli.stdout
    assert "Receipt        VALID" in cli.stdout
    assert "Engine         Native Core" in cli.stdout
    assert "Fallback       false" in cli.stdout


def test_real_native_denial_round_trip_preserves_diagnostic_and_capability_behavior(
    tmp_path: Path,
    native_binary: Path,
):
    (tmp_path / "secret.txt").write_text("not disclosed", encoding="utf-8")
    source = tmp_path / "denied.sona"
    source.write_text('import fs; print(fs.read_text("secret.txt"));\n', encoding="utf-8")

    normal = _native_run(native_binary, "run", str(source), "--engine", "native", cwd=tmp_path)
    receipt_path = tmp_path / "denied-proof.json"
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

    assert proof.returncode == normal.returncode == 1
    assert proof.stdout == normal.stdout
    assert proof.stderr == normal.stderr
    assert b"SONA-FS-005" in proof.stderr
    assert b"PROOF-" not in proof.stderr

    result = verify_receipt(receipt_path)
    _assert_native_engine(result)
    assert result["status"] == "valid"
    assert result["execution"]["status"] == "failed"
    assert result["execution"]["exit_code"] == 1
    assert result["execution"]["diagnostic"]["id"] == "SONA-FS-005"
    assert result["capabilities"]["filesystem_read"] is False
    assert result["effects"][0]["outcome"] == "denied"
    assert result["effects"][0]["effect"] == "FS.READ"
    assert result["effects"][0]["support"] == "SUPPORTED"


def test_real_native_clock_and_random_effects_round_trip_without_values(
    tmp_path: Path,
    native_binary: Path,
):
    source = tmp_path / "nondeterminism.sona"
    source.write_text(
        "import date; import time; import random; "
        "random.seed(734291037); random.integer(10, 99); random.float(); "
        "date.today(); time.monotonic();\n",
        encoding="utf-8",
    )
    receipt_path = tmp_path / "nondeterminism-proof.json"

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

    assert proof.returncode == 0, proof.stderr.decode("utf-8", "replace")
    result = verify_receipt(receipt_path)
    assert [
        (effect["effect"], effect["support"], effect["outcome"])
        for effect in result["effects"]
    ] == [
        ("RANDOM.SEED", "SUPPORTED", "allowed"),
        ("RANDOM.READ", "SUPPORTED", "allowed"),
        ("RANDOM.READ", "SUPPORTED", "allowed"),
        ("CLOCK.READ", "SUPPORTED", "allowed"),
        ("CLOCK.READ", "SUPPORTED", "allowed"),
    ]
    assert all("target" not in effect for effect in result["effects"])
    raw_receipt = receipt_path.read_text(encoding="utf-8")
    assert "734291037" not in raw_receipt
    assert "nondeterminism.sona" not in raw_receipt


def test_real_native_http_unavailability_is_recorded_without_request_data(
    tmp_path: Path,
    native_binary: Path,
):
    source = tmp_path / "network.sona"
    secret_url = "https://example.invalid/private?token=receipt-secret-0155"
    source.write_text(f'import http; http.get("{secret_url}");\n', encoding="utf-8")
    receipt_path = tmp_path / "network-proof.json"

    proof = _native_run(
        native_binary,
        "proof",
        str(source),
        "--receipt",
        str(receipt_path),
        "--engine",
        "native",
        "--allow-network",
        cwd=tmp_path,
    )

    assert proof.returncode == 1
    assert b"SONA-HTTP-005" in proof.stderr
    result = verify_receipt(receipt_path)
    assert result["capabilities"]["network"] is True
    assert result["execution"]["status"] == "failed"
    assert result["effects"] == [
        {
            "sequence": 1,
            "scope": "network",
            "operation": "http.get",
            "outcome": "unavailable",
            "effect": "NET.REQUEST",
            "support": "UNAVAILABLE",
        }
    ]
    raw_receipt = receipt_path.read_text(encoding="utf-8")
    assert secret_url not in raw_receipt
    assert "receipt-secret-0155" not in raw_receipt


def test_guardian_policy_allows_requested_native_proof_capability(
    tmp_path: Path,
    native_binary: Path,
):
    project = tmp_path / "guardian-allow"
    project.mkdir()
    private_output = "private-output-body-7429"
    (project / "input.txt").write_text(private_output, encoding="utf-8")
    source = project / "allowed.sona"
    source.write_text('import fs; print(fs.read_text("input.txt"));\n', encoding="utf-8")
    (project / "sona.guard.json").write_text(
        json.dumps({
            "schema_version": 1,
            "capabilities": {
                "filesystem_read": "allow",
                "filesystem_write": "deny",
                "network": "deny",
            },
        }),
        encoding="utf-8",
    )
    initialized = guardian.guardian_init(project)
    receipt_path = tmp_path / "guardian-allowed-proof.json"

    proof = _native_run(
        native_binary,
        "proof",
        str(source),
        "--receipt",
        str(receipt_path),
        "--engine",
        "native",
        "--allow-fs-read",
        "--guardian-root",
        str(project),
        cwd=project,
    )

    assert proof.returncode == 0, proof.stderr.decode("utf-8", "replace")
    assert proof.stdout == (private_output + "\n").encode("utf-8")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["capabilities"]["filesystem_read"] is True
    assert receipt["guardian"]["policy_enforced"] is True
    assert receipt["guardian"]["policy_sha256"] == initialized["policy_sha256"]
    verified = guardian.guardian_proof_verify(project, receipt_path)
    assert verified["status"] == "verified"
    assert verified["runtime_evidence"]["effects"] == verify_receipt(receipt_path)["effects"]

    reviewed = guardian.guardian_proof_review(project, receipt_path, "deterministic")
    assert reviewed["status"] == "reviewed"
    review_effects = reviewed["evidence"]["runtime_evidence"]["effects"]
    assert [
        (item["effect"], item["outcome"], item["support"])
        for item in review_effects
    ] == [
        ("FS.READ", "allowed", "SUPPORTED"),
        ("STDOUT.WRITE", "allowed", "PARTIAL"),
    ]
    assert all("target" not in item for item in review_effects)
    assert any("target" in item for item in receipt["effects"])
    rendered_review_input = json.dumps(reviewed["evidence"])
    assert "input.txt" not in rendered_review_input
    assert private_output not in rendered_review_input
    assert str(project) not in rendered_review_input
    assert reviewed["evidence"]["observation_boundary"] == {
        "effect_source": "instrumented-native-host-boundaries",
        "agent_action": "not-represented",
        "ai_request_causality": "not-established",
    }
    assert "FS.READ allowed" in reviewed["review"]
    assert "STDOUT.WRITE allowed" in reviewed["review"]
    assert "No AGENT.ACTION" in reviewed["review"]


def test_guardian_policy_denies_requested_native_proof_capability_and_records_effect(
    tmp_path: Path,
    native_binary: Path,
):
    project = tmp_path / "guardian-deny"
    project.mkdir()
    (project / "secret.txt").write_text("not disclosed", encoding="utf-8")
    source = project / "denied.sona"
    source.write_text('import fs; print(fs.read_text("secret.txt"));\n', encoding="utf-8")
    initialized = guardian.guardian_init(project)
    receipt_path = tmp_path / "guardian-denied-proof.json"

    proof = _native_run(
        native_binary,
        "proof",
        str(source),
        "--receipt",
        str(receipt_path),
        "--engine",
        "native",
        "--allow-fs-read",
        "--guardian-root",
        str(project),
        cwd=project,
    )

    assert proof.returncode == 1
    assert b"SONA-FS-005" in proof.stderr
    result = verify_receipt(receipt_path)
    assert result["capabilities"]["filesystem_read"] is False
    assert result["execution"]["diagnostic"]["id"] == "SONA-FS-005"
    assert any(
        effect["operation"] == "fs.read_text" and effect["outcome"] == "denied"
        for effect in result["effects"]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["guardian"]["policy_sha256"] == initialized["policy_sha256"]
    assert guardian.guardian_proof_verify(project, receipt_path)["status"] == "verified"


def test_guardian_policy_denies_requested_native_proof_filesystem_write(
    tmp_path: Path,
    native_binary: Path,
):
    project = tmp_path / "guardian-deny-write"
    project.mkdir()
    source = project / "denied-write.sona"
    source.write_text('import fs; fs.write_text("created.txt", "blocked");\n', encoding="utf-8")
    initialized = guardian.guardian_init(project)
    receipt_path = tmp_path / "guardian-denied-write-proof.json"

    proof = _native_run(
        native_binary,
        "proof",
        str(source),
        "--receipt",
        str(receipt_path),
        "--engine",
        "native",
        "--allow-fs-write",
        "--guardian-root",
        str(project),
        cwd=project,
    )

    assert proof.returncode == 1
    assert b"SONA-FS-005" in proof.stderr
    assert not (project / "created.txt").exists()
    result = verify_receipt(receipt_path)
    assert result["capabilities"]["filesystem_write"] is False
    assert result["execution"]["diagnostic"]["id"] == "SONA-FS-005"
    assert any(
        effect["operation"] == "fs.write_text" and effect["outcome"] == "denied"
        for effect in result["effects"]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["guardian"]["policy_sha256"] == initialized["policy_sha256"]
    assert guardian.guardian_proof_verify(project, receipt_path)["status"] == "verified"


def test_real_source_backed_sbc_round_trip_preserves_both_identities(
    tmp_path: Path,
    native_binary: Path,
):
    source = tmp_path / "container.sona"
    source.write_bytes(b'print("source-backed");\r\n')
    container = tmp_path / "container.sbc"
    compiled = _native_run(
        native_binary,
        "compile",
        str(source),
        "--output",
        str(container),
        cwd=tmp_path,
    )
    assert compiled.returncode == 0, compiled.stderr.decode("utf-8", "replace")

    normal = _native_run(native_binary, "exec", str(container), cwd=tmp_path)
    receipt_path = tmp_path / "container-proof.json"
    proof = _native_run(
        native_binary,
        "proof",
        str(container),
        "--receipt",
        str(receipt_path),
        "--engine",
        "native",
        cwd=tmp_path,
    )

    assert proof.returncode == normal.returncode == 0
    assert proof.stdout == normal.stdout == b"source-backed\n"
    assert proof.stderr == normal.stderr == b""

    result = verify_receipt(receipt_path)
    _assert_native_engine(result)
    assert result["program"] == {
        "kind": "sbc",
        "source": {"sha256": _sha256(source.read_bytes()), "bytes": len(source.read_bytes())},
        "container": {
            "sha256": _sha256(container.read_bytes()),
            "bytes": len(container.read_bytes()),
        },
    }
    assert result["execution"]["stdout"] == {
        "sha256": _sha256(proof.stdout),
        "bytes": len(proof.stdout),
    }


def test_actual_native_receipt_corruption_matrix_fails_closed(
    tmp_path: Path,
    native_binary: Path,
):
    source = tmp_path / "corruption.sona"
    source.write_text('print("matrix");\n', encoding="utf-8")
    source_receipt_path = tmp_path / "source.json"
    source_proof = _native_run(
        native_binary,
        "proof",
        str(source),
        "--receipt",
        str(source_receipt_path),
        cwd=tmp_path,
    )
    assert source_proof.returncode == 0
    verify_receipt(source_receipt_path)
    source_receipt = json.loads(source_receipt_path.read_bytes())

    container = tmp_path / "corruption.sbc"
    compiled = _native_run(
        native_binary,
        "compile",
        str(source),
        "--output",
        str(container),
        cwd=tmp_path,
    )
    assert compiled.returncode == 0
    container_receipt_path = tmp_path / "container.json"
    container_proof = _native_run(
        native_binary,
        "proof",
        str(container),
        "--receipt",
        str(container_receipt_path),
        cwd=tmp_path,
    )
    assert container_proof.returncode == 0
    verify_receipt(container_receipt_path)
    container_receipt = json.loads(container_receipt_path.read_bytes())

    def replace_source_hash(receipt: dict) -> None:
        receipt["program"]["source"]["sha256"] = "sha256:" + "f" * 64

    def replace_container_hash(receipt: dict) -> None:
        receipt["program"]["container"]["sha256"] = "sha256:" + "f" * 64

    def replace_execution_status(receipt: dict) -> None:
        receipt["execution"]["status"] = "failed"

    def replace_capability_grant(receipt: dict) -> None:
        receipt["capabilities"]["filesystem_read"] = not receipt["capabilities"]["filesystem_read"]

    def replace_effect_operation(receipt: dict) -> None:
        receipt["effects"][0]["operation"] = "tampered.operation"

    def replace_stdout_hash(receipt: dict) -> None:
        receipt["execution"]["stdout"]["sha256"] = "sha256:" + "f" * 64

    def replace_runtime_identity(receipt: dict) -> None:
        receipt["sona_version"] = "0.15.4-tampered"

    def enable_fallback(receipt: dict) -> None:
        receipt["engine"]["fallback_used"] = True

    def replace_receipt_hash(receipt: dict) -> None:
        receipt["receipt_hash"] = "sha256:" + "f" * 64

    mutations: list[tuple[str, dict, Callable[[dict], None]]] = [
        ("source-hash", source_receipt, replace_source_hash),
        ("container-hash", container_receipt, replace_container_hash),
        ("execution-status", source_receipt, replace_execution_status),
        ("capability-grant", source_receipt, replace_capability_grant),
        ("effect-operation", source_receipt, replace_effect_operation),
        ("stdout-hash", source_receipt, replace_stdout_hash),
        ("runtime-identity", source_receipt, replace_runtime_identity),
        ("fallback-used", source_receipt, enable_fallback),
        ("receipt-hash", source_receipt, replace_receipt_hash),
    ]

    for name, original, mutate in mutations:
        corrupted = copy.deepcopy(original)
        mutate(corrupted)
        path = tmp_path / f"corrupted-{name}.json"
        path.write_bytes(canonical_json_bytes(corrupted) + b"\n")
        with pytest.raises(ProofDiagnostic) as raised:
            verify_receipt(path)
        assert raised.value.diagnostic_id == "PROOF-VERIFY-005", name


def test_actual_native_receipt_enforces_canonical_storage_contract(
    tmp_path: Path,
    native_binary: Path,
):
    source = tmp_path / "canonical.sona"
    source.write_text('print("canonical");\n', encoding="utf-8")
    receipt_path = tmp_path / "canonical.json"
    proof = _native_run(
        native_binary,
        "proof",
        str(source),
        "--receipt",
        str(receipt_path),
        cwd=tmp_path,
    )
    assert proof.returncode == 0

    receipt = json.loads(receipt_path.read_bytes())
    canonical = canonical_json_bytes(receipt)
    assert receipt_path.read_bytes() == canonical + b"\n"

    accepted = {
        "no-newline": canonical,
        "one-lf": canonical + b"\n",
    }
    for name, raw in accepted.items():
        path = tmp_path / f"accepted-{name}.json"
        path.write_bytes(raw)
        assert verify_receipt(path)["status"] == "valid"

    reordered = json.dumps(
        dict(reversed(list(receipt.items()))),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    rejected = {
        "reordered-keys": reordered,
        "pretty-printed": json.dumps(receipt, ensure_ascii=False, indent=2).encode("utf-8"),
        "leading-whitespace": b" " + canonical,
        "trailing-space": canonical + b" ",
        "two-lfs": canonical + b"\n\n",
    }
    for name, raw in rejected.items():
        path = tmp_path / f"rejected-{name}.json"
        path.write_bytes(raw)
        with pytest.raises(ProofDiagnostic) as raised:
            verify_receipt(path)
        assert raised.value.diagnostic_id == "PROOF-VERIFY-004", name


def test_0154_native_schema1_fixture_remains_verifiable():
    result = verify_receipt(COMPAT_RECEIPT)

    assert result["status"] == "valid"
    assert result["schema_id"] == "sona.native-proof.schema-1"
    assert result["sona_version"] == "0.15.4"
    assert result["receipt_hash"] == (
        "sha256:5c7c05b26bcbff0fce7ac4c3caccb7ae6e74ca6c3af6d7b01ef306474e53805f"
    )
    _assert_native_engine(result, extended=False)
