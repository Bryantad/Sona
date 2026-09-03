import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from sona.proof import (
    EFFECT_CLASSIFICATIONS,
    EFFECT_SUPPORT_STATUSES,
    ProofDiagnostic,
    canonical_json_bytes,
    sha256_label,
    verify_receipt,
    verify_receipt_payload,
)

ROOT = Path(__file__).resolve().parents[2]
VECTOR_PATH = ROOT / "tests" / "proof" / "vectors" / "schema1-vectors.json"
EFFECT_VECTOR_PATH = ROOT / "tests" / "proof" / "vectors" / "effect-vocabulary.json"


def _seal(receipt: dict) -> dict:
    unsigned = dict(receipt)
    unsigned.pop("receipt_hash", None)
    receipt = dict(receipt)
    receipt["receipt_hash"] = sha256_label(canonical_json_bytes(unsigned))
    return receipt


def _receipt(**updates) -> dict:
    receipt = {
        "schema_id": "sona.native-proof.schema-1",
        "schema": 1,
        "receipt_type": "native_execution_proof",
        "generated_at_utc": "2026-08-20T00:00:00Z",
        "sona_version": "0.15.4",
        "engine": {
            "name": "native",
            "python_required": False,
            "python_embedded": False,
            "fallback_used": False,
        },
        "program": {
            "kind": "source",
            "source": {
                "sha256": sha256_label(b'print("hello")\n'),
                "bytes": len(b'print("hello")\n'),
            },
        },
        "capabilities": {
            "console": True,
            "filesystem_read": True,
            "filesystem_write": False,
            "network": False,
            "process": False,
            "environment": False,
        },
        "execution": {
            "status": "ok",
            "exit_code": 0,
            "duration_ms": 0,
            "diagnostic": None,
            "stdout": {"sha256": sha256_label(b"hello\n"), "bytes": 6},
            "stderr": {"sha256": sha256_label(b""), "bytes": 0},
        },
        "effects": [
            {
                "sequence": 1,
                "scope": "filesystem",
                "operation": "fs.read_text",
                "outcome": "allowed",
                "target": "hmac-sha256:" + "1" * 64,
            },
            {
                "sequence": 2,
                "scope": "console",
                "operation": "print",
                "outcome": "allowed",
            },
        ],
    }
    receipt.update(updates)
    return _seal(receipt)


def _write(path: Path, receipt: dict, *, canonical: bool = True) -> Path:
    if canonical:
        path.write_bytes(canonical_json_bytes(receipt) + b"\n")
    else:
        path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return path


def test_shared_schema1_vectors_lock_python_canonicalization_and_verification():
    corpus = json.loads(VECTOR_PATH.read_text(encoding="utf-8"))

    assert corpus["schema_id"] == "sona.proof-interoperability-vectors.schema-1"
    assert [vector["name"] for vector in corpus["vectors"]] == [
        "basic-success",
        "runtime-failure",
        "capability-denial",
        "filesystem-read",
    ]
    for vector in corpus["vectors"]:
        canonical_payload = vector["canonical_payload"].encode("utf-8")
        unsigned = json.loads(canonical_payload)
        assert canonical_json_bytes(unsigned) == canonical_payload
        assert sha256_label(canonical_payload) == vector["canonical_payload_sha256"]

        receipt = dict(unsigned)
        receipt["receipt_hash"] = vector["expected_receipt_hash"]
        raw = canonical_json_bytes(receipt) + b"\n"
        result = verify_receipt_payload(receipt, raw)
        assert result["status"] == vector["expected_verifier_outcome"]
        assert result["receipt_hash"] == vector["expected_receipt_hash"]


def test_shared_effect_vocabulary_locks_python_classification():
    corpus = json.loads(EFFECT_VECTOR_PATH.read_text(encoding="utf-8"))
    mappings = {
        (entry["scope"], entry["operation"]): (entry["effect"], entry["support"])
        for entry in corpus["mappings"]
    }

    assert corpus["schema_id"] == "sona.proof-effect-vocabulary.schema-1"
    assert set(corpus["support_statuses"]) == EFFECT_SUPPORT_STATUSES
    assert mappings == EFFECT_CLASSIFICATIONS
    assert "AGENT.ACTION" not in {effect for effect, _support in mappings.values()}
    assert corpus["unobserved"] == [
        {
            "effect": "NET.CONNECT",
            "support": "UNOBSERVED",
            "reason": "Native Core has no independently instrumented connection boundary.",
        }
    ]


def test_valid_receipt_verifies_capabilities_and_effects(tmp_path):
    path = _write(tmp_path / "proof.json", _receipt())

    result = verify_receipt(path)

    assert result["status"] == "valid"
    assert result["schema_id"] == "sona.native-proof.schema-1"
    assert result["engine"]["label"] == "Native Core"
    assert result["engine"]["fallback_used"] is False
    assert result["capabilities"]["filesystem_read"] is True
    assert result["capabilities"]["filesystem_write"] is False
    assert result["effects"][0]["scope"] == "filesystem"
    assert result["effects"][0]["effect"] == "FS.READ"
    assert result["effects"][0]["support"] == "SUPPORTED"
    assert result["effects"][1]["operation"] == "print"
    assert result["effects"][1]["effect"] == "STDOUT.WRITE"
    assert result["effects"][1]["support"] == "PARTIAL"


def test_optional_native_runtime_identity_is_validated_and_exposed(tmp_path):
    engine = {
        "name": "native",
        "python_required": False,
        "python_embedded": False,
        "fallback_used": False,
        "runtime_identity": {
            "native_binary": {
                "sha256": "sha256:" + "2" * 64,
                "bytes": 123456,
            },
            "source_revision": "git:" + "1" * 40,
        },
    }
    path = _write(tmp_path / "identity-proof.json", _receipt(engine=engine))

    result = verify_receipt(path)

    assert result["engine"]["runtime_identity"] == engine["runtime_identity"]


@pytest.mark.parametrize(
    ("runtime_identity", "diagnostic_id"),
    [
        ({}, "PROOF-VERIFY-038"),
        (
            {"native_binary": {"sha256": "sha256:bad", "bytes": 4}},
            "PROOF-VERIFY-038",
        ),
        (
            {
                "native_binary": {"sha256": "sha256:" + "2" * 64, "bytes": 4},
                "source_revision": "git:short",
            },
            "PROOF-VERIFY-039",
        ),
    ],
)
def test_invalid_optional_native_runtime_identity_is_rejected(
    tmp_path, runtime_identity, diagnostic_id
):
    engine = {
        "name": "native",
        "python_required": False,
        "python_embedded": False,
        "fallback_used": False,
        "runtime_identity": runtime_identity,
    }
    path = _write(tmp_path / "invalid-identity.json", _receipt(engine=engine))

    with pytest.raises(ProofDiagnostic) as raised:
        verify_receipt(path)

    assert raised.value.diagnostic_id == diagnostic_id


def test_explicit_normalized_effect_mapping_is_accepted(tmp_path):
    receipt = _receipt()
    receipt["effects"][0]["effect"] = "FS.READ"
    receipt["effects"][0]["support"] = "SUPPORTED"
    path = _write(tmp_path / "proof.json", _seal(receipt))

    result = verify_receipt(path)

    assert result["effects"][0]["effect"] == "FS.READ"
    assert result["effects"][0]["support"] == "SUPPORTED"


@pytest.mark.parametrize("missing", ["effect", "support"])
def test_incomplete_normalized_effect_mapping_is_rejected(tmp_path, missing):
    receipt = _receipt()
    receipt["effects"][0].update({"effect": "FS.READ", "support": "SUPPORTED"})
    receipt["effects"][0].pop(missing)
    path = _write(tmp_path / "proof.json", _seal(receipt))

    with pytest.raises(ProofDiagnostic) as raised:
        verify_receipt(path)

    assert raised.value.diagnostic_id == "PROOF-VERIFY-035"


@pytest.mark.parametrize(
    ("effect", "support"),
    [
        ("fs.read", "SUPPORTED"),
        ("FS.READ", "experimental"),
    ],
)
def test_invalid_normalized_effect_fields_are_rejected(tmp_path, effect, support):
    receipt = _receipt()
    receipt["effects"][0].update({"effect": effect, "support": support})
    path = _write(tmp_path / "proof.json", _seal(receipt))

    with pytest.raises(ProofDiagnostic) as raised:
        verify_receipt(path)

    assert raised.value.diagnostic_id == "PROOF-VERIFY-036"


def test_mismatched_normalized_effect_mapping_is_rejected(tmp_path):
    receipt = _receipt()
    receipt["effects"][0].update({"effect": "FS.WRITE", "support": "PARTIAL"})
    path = _write(tmp_path / "proof.json", _seal(receipt))

    with pytest.raises(ProofDiagnostic) as raised:
        verify_receipt(path)

    assert raised.value.diagnostic_id == "PROOF-VERIFY-037"


def test_unknown_legacy_operation_remains_structurally_valid(tmp_path):
    receipt = _receipt(
        effects=[
            {
                "sequence": 1,
                "scope": "future-runtime",
                "operation": "future.operation",
                "outcome": "allowed",
            }
        ]
    )
    path = _write(tmp_path / "proof.json", receipt)

    result = verify_receipt(path)

    assert result["effects"] == [
        {
            "sequence": 1,
            "scope": "future-runtime",
            "operation": "future.operation",
            "outcome": "allowed",
        }
    ]


def test_unknown_operation_cannot_claim_a_registered_effect(tmp_path):
    receipt = _receipt(
        effects=[
            {
                "sequence": 1,
                "scope": "future-runtime",
                "operation": "future.operation",
                "outcome": "allowed",
                "effect": "FS.READ",
                "support": "SUPPORTED",
            }
        ]
    )
    path = _write(tmp_path / "proof.json", receipt)

    with pytest.raises(ProofDiagnostic) as raised:
        verify_receipt(path)

    assert raised.value.diagnostic_id == "PROOF-VERIFY-037"


def test_corrupted_receipt_fails_safely(tmp_path):
    path = tmp_path / "proof.json"
    path.write_bytes(b"{not json")

    with pytest.raises(ProofDiagnostic) as raised:
        verify_receipt(path)

    assert raised.value.diagnostic_id == "PROOF-VERIFY-002"
    assert "receipt could not be read safely" in raised.value.message.lower()


def test_invalid_schema_is_rejected(tmp_path):
    path = _write(tmp_path / "proof.json", _receipt(schema=2))

    with pytest.raises(ProofDiagnostic) as raised:
        verify_receipt(path)

    assert raised.value.diagnostic_id == "PROOF-VERIFY-007"


def test_missing_required_fields_are_rejected(tmp_path):
    receipt = _receipt()
    receipt.pop("execution")
    receipt = _seal(receipt)
    path = _write(tmp_path / "proof.json", receipt)

    with pytest.raises(ProofDiagnostic) as raised:
        verify_receipt(path)

    assert raised.value.diagnostic_id == "PROOF-VERIFY-006"


def test_hash_mismatch_is_rejected(tmp_path):
    receipt = _receipt()
    receipt["sona_version"] = "tampered"
    path = _write(tmp_path / "proof.json", receipt)

    with pytest.raises(ProofDiagnostic) as raised:
        verify_receipt(path)

    assert raised.value.diagnostic_id == "PROOF-VERIFY-005"


def test_noncanonical_receipt_is_rejected(tmp_path):
    path = _write(tmp_path / "proof.json", _receipt(), canonical=False)

    with pytest.raises(ProofDiagnostic) as raised:
        verify_receipt(path)

    assert raised.value.diagnostic_id == "PROOF-VERIFY-004"


def test_capability_capture_requires_explicit_booleans(tmp_path):
    receipt = _receipt(capabilities={"console": True})
    path = _write(tmp_path / "proof.json", receipt)

    with pytest.raises(ProofDiagnostic) as raised:
        verify_receipt(path)

    assert raised.value.diagnostic_id == "PROOF-VERIFY-015"


def test_effect_capture_requires_contiguous_redacted_records(tmp_path):
    receipt = _receipt(
        effects=[
            {
                "sequence": 2,
                "scope": "filesystem",
                "operation": "fs.read_text",
                "outcome": "allowed",
                "target": "C:/raw/path.txt",
            }
        ]
    )
    path = _write(tmp_path / "proof.json", receipt)

    with pytest.raises(ProofDiagnostic) as raised:
        verify_receipt(path)

    assert raised.value.diagnostic_id == "PROOF-VERIFY-025"


def test_no_python_proof_identity_is_required(tmp_path):
    path = _write(
        tmp_path / "proof.json",
        _receipt(engine={"name": "native", "python_required": True, "python_embedded": False, "fallback_used": False}),
    )

    with pytest.raises(ProofDiagnostic) as raised:
        verify_receipt(path)

    assert raised.value.diagnostic_id == "PROOF-VERIFY-012"


def test_fallback_rejection(tmp_path):
    path = _write(
        tmp_path / "proof.json",
        _receipt(engine={"name": "native", "python_required": False, "python_embedded": False, "fallback_used": True}),
    )

    with pytest.raises(ProofDiagnostic) as raised:
        verify_receipt(path)

    assert raised.value.diagnostic_id == "PROOF-VERIFY-013"


def test_proof_verify_cli_outputs_professional_summary(tmp_path):
    path = _write(tmp_path / "proof.json", _receipt())
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)

    process = subprocess.run(
        [sys.executable, "-m", "sona", "proof", "verify", str(path)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )

    assert process.returncode == 0, process.stderr or process.stdout
    assert "Proof Mode Verification" in process.stdout
    assert "Receipt        VALID" in process.stdout
    assert "Integrity      VALID" in process.stdout
    assert "Execution      SUCCEEDED (exit 0)" in process.stdout
    assert "Program        source" in process.stdout
    assert "Runtime        Sona 0.15.4" in process.stdout
    assert "Engine         Native Core" in process.stdout
    assert "Python         not involved in recorded execution" in process.stdout
    assert "Fallback       false" in process.stdout
    assert "Capabilities" in process.stdout
    assert "Observed effects" in process.stdout
    assert "- fs.read" in process.stdout
    assert "FS.READ" in process.stdout
    assert "STDOUT.WRITE" in process.stdout
    assert "(SUPPORTED)" in process.stdout
    assert "(PARTIAL)" in process.stdout
    assert "Program identity" in process.stdout
    assert sha256_label(b'print("hello")\n') in process.stdout
    assert "Output identity" in process.stdout
    assert sha256_label(b"hello\n") in process.stdout
    assert "Receipt identity" in process.stdout


def test_proof_inspect_cli_outputs_normalized_effects(tmp_path):
    path = _write(tmp_path / "proof.json", _receipt())
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)

    process = subprocess.run(
        [sys.executable, "-m", "sona", "proof", "inspect", str(path)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )

    assert process.returncode == 0, process.stderr or process.stdout
    assert "Proof Mode Inspection" in process.stdout
    assert "Receipt        VALID" in process.stdout
    assert "Integrity      VALID" in process.stdout
    assert "Execution      SUCCEEDED (exit 0)" in process.stdout
    assert "Runtime        Sona 0.15.4" in process.stdout
    assert "Python         not involved in recorded execution" in process.stdout
    assert "Fallback       false" in process.stdout
    assert "Capabilities" in process.stdout
    assert "Observed effects" in process.stdout
    assert "FS.READ" in process.stdout
    assert "STDOUT.WRITE" in process.stdout
    assert "Program identity" in process.stdout
    assert "Output identity" in process.stdout
    assert "Receipt identity" in process.stdout


def test_proof_inspect_cli_returns_json_for_invalid_receipts(tmp_path):
    path = tmp_path / "proof.json"
    path.write_text("[]", encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)

    process = subprocess.run(
        [sys.executable, "-m", "sona", "proof", "inspect", str(path), "--json"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )

    assert process.returncode == 1
    payload = json.loads(process.stdout)
    assert payload["status"] == "invalid"
    assert payload["diagnostic"]["diagnostic_id"] == "PROOF-VERIFY-003"
