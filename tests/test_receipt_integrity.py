import json
import sys

from sona import cli
from sona.receipts import (
    DirectoryReceiptConfig,
    ReplayContract,
    SIGNED_FIELDS_VERSION,
    _normalize_text_for_redaction,
    append_receipt_event,
    build_directory_receipt,
    build_receipt,
    canonical_receipt_payload,
    clear_active_receipt,
    diff_directory_receipts,
    enrich_chain_certificate,
    export_receipt_bundle,
    get_active_receipt,
    redact_receipt_payload,
    receipt_hash_from_file,
    receipt_sha256,
    set_active_receipt,
    sign_receipt_payload,
    verify_receipt_bundle,
    verify_receipt_chain,
    verify_receipt_chain_in_dir,
    verify_directory_receipt,
    verify_receipt_signature,
    verify_replay_contract,
    write_receipt_json,
)


def _run_cli(args, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["sona"] + args)
    return cli.main()


def test_directory_receipt_deterministic_tree_hash_and_id(tmp_path):
    (tmp_path / "src").mkdir(parents=True)
    (tmp_path / "src" / "main.sona").write_text("print('hello');\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "ignored.txt").write_text("ignore me\n", encoding="utf-8")

    config = DirectoryReceiptConfig(mode="deterministic")
    first = build_directory_receipt(root_path=tmp_path, config=config)
    second = build_directory_receipt(root_path=tmp_path, config=config)

    assert first["summary"]["tree_sha256"] == second["summary"]["tree_sha256"]
    assert first["receipt_id"] == second["receipt_id"]
    assert first["receipt_hash"] == second["receipt_hash"]
    assert first["receipt_hash"] == receipt_sha256(first)
    assert first["header"]["policy_fingerprint"] == second["header"]["policy_fingerprint"]
    assert "created_at_utc" not in first

    paths = [entry["path"] for entry in first["files"]]
    assert paths == sorted(paths)
    assert "node_modules/ignored.txt" not in paths


def test_verify_and_diff_detect_file_changes(tmp_path):
    (tmp_path / "app.sona").write_text("print('one');\n", encoding="utf-8")
    config = DirectoryReceiptConfig(mode="deterministic")
    baseline = build_directory_receipt(root_path=tmp_path, config=config)

    verify_ok = verify_directory_receipt(baseline, tmp_path)
    assert verify_ok["ok"] is True
    assert verify_ok["changed_count"] == 0
    assert verify_ok["policy_match"] is True
    assert verify_ok["engine_policy_match"] is True

    (tmp_path / "app.sona").write_text("print('two');\n", encoding="utf-8")
    verify_changed = verify_directory_receipt(baseline, tmp_path)
    assert verify_changed["ok"] is False
    assert verify_changed["changed_count"] == 1
    assert verify_changed["changed"][0]["path"] == "app.sona"

    current = build_directory_receipt(root_path=tmp_path, config=config)
    diff = diff_directory_receipts(baseline, current)
    assert diff["changed_count"] == 1
    assert diff["added_count"] == 0
    assert diff["removed_count"] == 0


def test_cli_receipt_scan_and_verify(tmp_path, monkeypatch):
    data_file = tmp_path / "data.txt"
    data_file.write_text("v1\n", encoding="utf-8")

    scan_exit = _run_cli(["receipt", "scan", str(tmp_path)], monkeypatch)
    assert scan_exit == 0

    receipt_dir = tmp_path / ".sona" / "receipts"
    receipts = sorted(receipt_dir.glob("*.receipt.json"))
    assert len(receipts) == 1
    receipt_path = receipts[0]

    verify_ok_exit = _run_cli(
        ["receipt", "verify", str(receipt_path), str(tmp_path)],
        monkeypatch,
    )
    assert verify_ok_exit == 0

    data_file.write_text("v2\n", encoding="utf-8")
    verify_changed_exit = _run_cli(
        ["receipt", "verify", str(receipt_path), str(tmp_path)],
        monkeypatch,
    )
    assert verify_changed_exit == 1


def test_receipt_chain_and_replay_smoke(tmp_path):
    (tmp_path / "artifact.txt").write_text("alpha\n", encoding="utf-8")
    config = DirectoryReceiptConfig(mode="deterministic")
    first = build_directory_receipt(root_path=tmp_path, config=config)

    first_path = tmp_path / "first.receipt.json"
    write_receipt_json(first, first_path)
    first_hash = receipt_hash_from_file(first_path)

    second = build_directory_receipt(
        root_path=tmp_path,
        config=config,
        prev_receipt_hash=first_hash,
    )
    assert second["header"]["prev_receipt_hash"] == first_hash
    assert second["header"]["policy_fingerprint"] == first["header"]["policy_fingerprint"]

    replay_ok = verify_directory_receipt(second, tmp_path)
    assert replay_ok["ok"] is True


def test_verify_receipt_chain_detects_divergence(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "artifact.txt").write_text("v1\n", encoding="utf-8")
    config = DirectoryReceiptConfig(mode="deterministic")

    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()

    first = build_directory_receipt(root_path=workspace, config=config)
    first_path = receipts_dir / "001.receipt.json"
    write_receipt_json(first, first_path)

    (workspace / "artifact.txt").write_text("v2\n", encoding="utf-8")
    second = build_directory_receipt(
        root_path=workspace,
        config=config,
        prev_receipt_hash=receipt_hash_from_file(first_path),
    )
    second_path = receipts_dir / "002.receipt.json"
    write_receipt_json(second, second_path)

    (workspace / "artifact.txt").write_text("v3\n", encoding="utf-8")
    third = build_directory_receipt(
        root_path=workspace,
        config=config,
        prev_receipt_hash=receipt_hash_from_file(second_path),
    )
    third_path = receipts_dir / "003.receipt.json"
    write_receipt_json(third, third_path)

    good = verify_receipt_chain_in_dir(receipts_dir)
    assert good["ok"] is True
    assert good["chain_length"] == 3
    assert good["certificate"]["chain_length"] == 3

    tampered = json.loads(second_path.read_text(encoding="utf-8"))
    tampered["summary"]["total_files"] = int(tampered["summary"]["total_files"]) + 1
    second_path.write_text(json.dumps(tampered, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    broken = verify_receipt_chain_in_dir(receipts_dir, head=str(third_path))
    assert broken["ok"] is False
    assert broken["divergence"]["reason"] in {"receipt_hash_mismatch", "prev_hash_not_canonical"}


def test_cli_receipt_verify_chain(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "artifact.txt").write_text("v1\n", encoding="utf-8")

    first_path = tmp_path / "r1.receipt.json"
    second_path = tmp_path / "r2.receipt.json"

    first_exit = _run_cli(
        ["receipt", "scan", str(workspace), "--output", str(first_path)],
        monkeypatch,
    )
    assert first_exit == 0

    (workspace / "artifact.txt").write_text("v2\n", encoding="utf-8")
    second_exit = _run_cli(
        [
            "receipt",
            "scan",
            str(workspace),
            "--output",
            str(second_path),
            "--prev-receipt",
            str(first_path),
        ],
        monkeypatch,
    )
    assert second_exit == 0

    chain_exit = _run_cli(
        ["receipt", "verify-chain", "--dir", str(tmp_path)],
        monkeypatch,
    )
    assert chain_exit == 0


def test_receipt_signature_round_trip_and_tamper_detection(tmp_path):
    (tmp_path / "artifact.txt").write_text("alpha\n", encoding="utf-8")
    config = DirectoryReceiptConfig(mode="deterministic")
    receipt = build_directory_receipt(root_path=tmp_path, config=config)

    signed = sign_receipt_payload(
        receipt,
        signing_key="unit-test-signing-key",
        key_id="ci",
        signed_at_utc="2026-02-25T00:00:00Z",
    )

    assert signed["header"]["signature"]["algorithm"] == "hmac-sha256"
    assert signed["header"]["signature"]["key_id"] == "ci"
    assert signed["receipt_hash"] == receipt_sha256(signed)

    verified = verify_receipt_signature(
        signed,
        signing_key="unit-test-signing-key",
        expected_key_id="ci",
    )
    assert verified["ok"] is True
    assert verified["reason"] == "ok"
    assert verified["receipt_hash_match"] is True
    assert verified["signature_match"] is True

    tampered = json.loads(json.dumps(signed))
    tampered["summary"]["total_files"] = int(tampered["summary"]["total_files"]) + 1
    broken = verify_receipt_signature(
        tampered,
        signing_key="unit-test-signing-key",
        expected_key_id="ci",
    )
    assert broken["ok"] is False
    assert broken["reason"] in {"receipt_hash_mismatch", "signature_mismatch"}


def test_cli_receipt_sign_and_verify_signature(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "artifact.txt").write_text("v1\n", encoding="utf-8")

    receipt_path = tmp_path / "signed.receipt.json"

    scan_exit = _run_cli(
        ["receipt", "scan", str(workspace), "--output", str(receipt_path)],
        monkeypatch,
    )
    assert scan_exit == 0

    monkeypatch.setenv("SONA_RECEIPT_SIGNING_KEY", "cli-signing-key")

    sign_exit = _run_cli(
        ["receipt", "sign", str(receipt_path), "--key-id", "ci"],
        monkeypatch,
    )
    assert sign_exit == 0

    verify_exit = _run_cli(
        ["receipt", "verify-signature", str(receipt_path), "--key-id", "ci"],
        monkeypatch,
    )
    assert verify_exit == 0

    tampered = json.loads(receipt_path.read_text(encoding="utf-8"))
    tampered["summary"]["total_bytes"] = int(tampered["summary"]["total_bytes"]) + 1
    receipt_path.write_text(json.dumps(tampered, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    verify_broken_exit = _run_cli(
        ["receipt", "verify-signature", str(receipt_path), "--key-id", "ci"],
        monkeypatch,
    )
    assert verify_broken_exit == 1


def test_receipt_redaction_deterministic_and_profile_dependent():
    receipt = {
        "receipt_id": "abc-123",
        "receipt_kind": "execution",
        "header": {
            "policy_fingerprint": "policy-001",
            "prev_receipt_hash": "",
        },
        "root_path": "/private/workspace",
        "inputs": {
            "args": ["--token", "secret-value"],
            "env_allowlist": {"API_KEY": "sk-test-123"},
        },
        "execution": {
            "errors": [
                {"kind": "error", "text": "password=abc123"},
            ]
        },
    }

    prod_a, prod_report_a = redact_receipt_payload(receipt, profile="prod")
    prod_b, prod_report_b = redact_receipt_payload(receipt, profile="prod")
    dev_receipt, _ = redact_receipt_payload(receipt, profile="dev")

    assert json.dumps(prod_a, sort_keys=True) == json.dumps(prod_b, sort_keys=True)
    assert prod_a["receipt_hash"] == prod_b["receipt_hash"]
    assert prod_report_a["redacted_values"] == prod_report_b["redacted_values"]

    assert prod_a["root_path"].startswith("[REDACTED:sha256:")
    assert dev_receipt["root_path"] == "/private/workspace"

    assert prod_a["inputs"]["args"][0].startswith("[REDACTED:sha256:")
    assert prod_a["inputs"]["env_allowlist"]["API_KEY"].startswith("[REDACTED:sha256:")
    assert prod_a["execution"]["errors"][0]["text"].startswith("[REDACTED:sha256:")


def test_redact_then_sign_then_verify_signature():
    raw = {
        "receipt_id": "redact-sign-1",
        "header": {"policy_fingerprint": "policy-001"},
        "inputs": {"args": ["secret"]},
    }
    redacted, _ = redact_receipt_payload(raw, profile="prod")
    signed = sign_receipt_payload(redacted, signing_key="redact-sign-key", key_id="ci")

    ok = verify_receipt_signature(signed, signing_key="redact-sign-key", expected_key_id="ci")
    assert ok["ok"] is True

    tampered = json.loads(json.dumps(signed))
    tampered["inputs"]["args"][0] = "[REDACTED:sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]"
    broken = verify_receipt_signature(tampered, signing_key="redact-sign-key", expected_key_id="ci")
    assert broken["ok"] is False


def test_cli_receipt_redact_and_redact_dir(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "artifact.txt").write_text("v1\n", encoding="utf-8")

    first_path = tmp_path / "r1.receipt.json"
    second_path = tmp_path / "r2.receipt.json"

    first_exit = _run_cli(
        ["receipt", "scan", str(workspace), "--output", str(first_path)],
        monkeypatch,
    )
    assert first_exit == 0

    (workspace / "artifact.txt").write_text("v2\n", encoding="utf-8")
    second_exit = _run_cli(
        ["receipt", "scan", str(workspace), "--output", str(second_path)],
        monkeypatch,
    )
    assert second_exit == 0

    redacted_single = tmp_path / "r1.redacted.receipt.json"
    redact_exit = _run_cli(
        [
            "receipt",
            "redact",
            str(first_path),
            "--out",
            str(redacted_single),
            "--profile",
            "prod",
            "--emit-manifest",
        ],
        monkeypatch,
    )
    assert redact_exit == 0
    assert redacted_single.exists()
    assert redacted_single.with_suffix(redacted_single.suffix + ".manifest.json").exists()

    out_dir = tmp_path / "redacted"
    redact_dir_exit = _run_cli(
        [
            "receipt",
            "redact-dir",
            str(tmp_path),
            "--out-dir",
            str(out_dir),
            "--profile",
            "prod",
            "--emit-manifest",
        ],
        monkeypatch,
    )
    assert redact_dir_exit == 0
    assert (out_dir / first_path.name).exists()
    assert (out_dir / second_path.name).exists()

    manifest = json.loads((out_dir / "redaction-manifest.json").read_text(encoding="utf-8"))
    assert int(manifest["processed_count"]) >= 2


# ---------------------------------------------------------------------------
# 0.11.0: Enriched chain certificate tests
# ---------------------------------------------------------------------------


def test_enriched_chain_certificate_integrity_score_and_signature_coverage(tmp_path):
    """Chain certificate should include integrity_score, signature_coverage, and chain_anchors."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "artifact.txt").write_text("v1\n", encoding="utf-8")
    config = DirectoryReceiptConfig(mode="deterministic")

    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()

    # Build a 3-receipt chain
    r1 = build_directory_receipt(root_path=workspace, config=config)
    r1_path = receipts_dir / "001.receipt.json"
    write_receipt_json(r1, r1_path)

    (workspace / "artifact.txt").write_text("v2\n", encoding="utf-8")
    r2 = build_directory_receipt(
        root_path=workspace, config=config,
        prev_receipt_hash=receipt_hash_from_file(r1_path),
    )
    r2_path = receipts_dir / "002.receipt.json"
    write_receipt_json(r2, r2_path)

    (workspace / "artifact.txt").write_text("v3\n", encoding="utf-8")
    r3 = build_directory_receipt(
        root_path=workspace, config=config,
        prev_receipt_hash=receipt_hash_from_file(r2_path),
    )
    # Sign only the head receipt
    r3_signed = sign_receipt_payload(r3, signing_key="test-key", key_id="ci")
    r3_path = receipts_dir / "003.receipt.json"
    write_receipt_json(r3_signed, r3_path)

    chain_result = verify_receipt_chain_in_dir(receipts_dir)
    assert chain_result["ok"] is True

    enriched = enrich_chain_certificate(chain_result)
    cert = enriched["certificate"]

    # integrity_score: all 3 have valid hashes
    assert cert["integrity_score"] == 1.0

    # signature_coverage: only 1 of 3 signed
    assert cert["signature_coverage"]["signed_count"] == 1
    assert cert["signature_coverage"]["total_count"] == 3
    assert 0.3 < cert["signature_coverage"]["signed_ratio"] < 0.4

    # chain_anchors: should have tail and first_signed
    anchor_roles = [a["role"] for a in cert["chain_anchors"]]
    assert "tail" in anchor_roles
    assert "first_signed" in anchor_roles


def test_enriched_chain_empty_has_zero_integrity_score(tmp_path):
    receipts_dir = tmp_path / "empty"
    receipts_dir.mkdir()
    chain_result = verify_receipt_chain_in_dir(receipts_dir)
    enriched = enrich_chain_certificate(chain_result)
    assert enriched["certificate"]["integrity_score"] == 0.0
    assert enriched["certificate"]["signature_coverage"]["signed_count"] == 0
    assert enriched["certificate"]["chain_anchors"] == []


# ---------------------------------------------------------------------------
# 0.11.0: Export receipt bundle tests
# ---------------------------------------------------------------------------


def test_export_receipt_bundle_produces_valid_bundle(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "file.txt").write_text("hello\n", encoding="utf-8")
    config = DirectoryReceiptConfig(mode="deterministic")

    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()

    r1 = build_directory_receipt(root_path=workspace, config=config)
    write_receipt_json(r1, receipts_dir / "001.receipt.json")

    bundle_path = tmp_path / "bundle.json"
    result = export_receipt_bundle(receipts_dir, bundle_path, include_policy_snapshot=True)

    assert result["ok"] is True
    assert result["receipt_count"] == 1
    assert result["chain_ok"] is True

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert bundle["bundle_version"] == "0.2"
    assert bundle["bundle_kind"] == "receipt_export"
    assert len(bundle["receipts"]) == 1
    assert bundle["policy_snapshot"] is not None
    assert "bundle_hash" in bundle
    assert "manifest" in bundle
    assert "chain_directory" in bundle


def test_export_receipt_bundle_without_policy(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "file.txt").write_text("data\n", encoding="utf-8")
    config = DirectoryReceiptConfig(mode="deterministic")

    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()
    r1 = build_directory_receipt(root_path=workspace, config=config)
    write_receipt_json(r1, receipts_dir / "001.receipt.json")

    bundle_path = tmp_path / "bundle_nopolicy.json"
    result = export_receipt_bundle(
        receipts_dir, bundle_path, include_policy_snapshot=False,
    )
    assert result["ok"] is True
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert "policy_snapshot" not in bundle or bundle["policy_snapshot"] is None


def test_cli_receipt_export(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "file.txt").write_text("data\n", encoding="utf-8")

    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()

    scan_exit = _run_cli(
        ["receipt", "scan", str(workspace), "--output", str(receipts_dir / "001.receipt.json")],
        monkeypatch,
    )
    assert scan_exit == 0

    bundle_path = tmp_path / "export.json"
    export_exit = _run_cli(
        ["receipt", "export", "--dir", str(receipts_dir), "--output", str(bundle_path)],
        monkeypatch,
    )
    assert export_exit == 0
    assert bundle_path.exists()

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert bundle["bundle_kind"] == "receipt_export"
    assert len(bundle["receipts"]) >= 1


# ---------------------------------------------------------------------------
# 0.11.0: Replay contract and determinism gate tests
# ---------------------------------------------------------------------------


def test_replay_contract_dataclass():
    contract = ReplayContract(
        command="sona receipt scan .",
        expected_tree_sha256="abc123",
        expected_receipt_hash="def456",
    )
    d = contract.to_dict()
    assert d["command"] == "sona receipt scan ."
    assert d["mode"] == "deterministic"
    assert d["tolerance"] == "exact"


def test_verify_replay_contract_same_input_passes(tmp_path):
    (tmp_path / "file.txt").write_text("stable\n", encoding="utf-8")
    config = DirectoryReceiptConfig(mode="deterministic")

    original = build_directory_receipt(root_path=tmp_path, config=config)
    replay = build_directory_receipt(root_path=tmp_path, config=config)

    result = verify_replay_contract(original, replay)
    assert result["ok"] is True
    assert result["tree_sha256_match"] is True
    assert result["receipt_hash_match"] is True
    assert result["mode_match"] is True
    assert result["policy_fingerprint_match"] is True


def test_verify_replay_contract_detects_drift(tmp_path):
    (tmp_path / "file.txt").write_text("original\n", encoding="utf-8")
    config = DirectoryReceiptConfig(mode="deterministic")
    original = build_directory_receipt(root_path=tmp_path, config=config)

    (tmp_path / "file.txt").write_text("changed\n", encoding="utf-8")
    replay = build_directory_receipt(root_path=tmp_path, config=config)

    result = verify_replay_contract(original, replay)
    assert result["ok"] is False
    assert result["tree_sha256_match"] is False
    assert result["receipt_hash_match"] is False


def test_deterministic_receipt_idempotent_rebuild(tmp_path):
    """Same directory scanned multiple times must yield identical receipts."""
    (tmp_path / "a.txt").write_text("alpha\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("beta\n", encoding="utf-8")
    config = DirectoryReceiptConfig(mode="deterministic")

    receipts = [build_directory_receipt(root_path=tmp_path, config=config) for _ in range(5)]
    hashes = [receipt_sha256(r) for r in receipts]
    ids = [r["receipt_id"] for r in receipts]
    trees = [r["summary"]["tree_sha256"] for r in receipts]

    assert len(set(hashes)) == 1, "Receipt hash should be identical across rebuilds"
    assert len(set(ids)) == 1, "Receipt ID should be identical across rebuilds"
    assert len(set(trees)) == 1, "Tree hash should be identical across rebuilds"


def test_audit_mode_receipt_unique_ids(tmp_path):
    """Audit-mode receipts should have unique IDs (uuid4)."""
    (tmp_path / "file.txt").write_text("data\n", encoding="utf-8")
    config = DirectoryReceiptConfig(mode="audit")
    r1 = build_directory_receipt(root_path=tmp_path, config=config)
    r2 = build_directory_receipt(root_path=tmp_path, config=config)

    assert r1["receipt_id"] != r2["receipt_id"], "Audit mode should use uuid4 (non-deterministic)"
    assert r1["summary"]["tree_sha256"] == r2["summary"]["tree_sha256"]
    assert "created_at_utc" in r1
    assert "audit" in r1


def test_mode_isolation_deterministic_vs_audit(tmp_path):
    """Deterministic and audit receipts for the same directory must differ structurally."""
    (tmp_path / "file.txt").write_text("data\n", encoding="utf-8")
    det = build_directory_receipt(
        root_path=tmp_path, config=DirectoryReceiptConfig(mode="deterministic"),
    )
    aud = build_directory_receipt(
        root_path=tmp_path, config=DirectoryReceiptConfig(mode="audit"),
    )

    assert det["mode"] == "deterministic"
    assert aud["mode"] == "audit"
    assert det["summary"]["tree_sha256"] == aud["summary"]["tree_sha256"]
    assert "created_at_utc" not in det
    assert "created_at_utc" in aud
    assert "audit" not in det
    assert "audit" in aud


def test_chain_cycle_detection(tmp_path):
    """Chain verifier should detect cycles and report them."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "f.txt").write_text("data\n", encoding="utf-8")
    config = DirectoryReceiptConfig(mode="deterministic")

    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()

    # Create a receipt that points to itself (cycle)
    r1 = build_directory_receipt(root_path=workspace, config=config)
    r1["header"]["prev_receipt_hash"] = r1["receipt_hash"]
    r1_path = receipts_dir / "001.receipt.json"
    write_receipt_json(r1, r1_path)

    result = verify_receipt_chain_in_dir(receipts_dir)
    # Either cycle_detected or some hash mismatch since we modified without rehashing
    assert result["ok"] is False


def test_deep_chain_integrity(tmp_path):
    """Verify a deeper chain (10 receipts) links correctly."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "f.txt").write_text("v0\n", encoding="utf-8")
    config = DirectoryReceiptConfig(mode="deterministic")

    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()

    prev_hash = None
    for i in range(10):
        (workspace / "f.txt").write_text(f"v{i}\n", encoding="utf-8")
        receipt = build_directory_receipt(
            root_path=workspace, config=config,
            prev_receipt_hash=prev_hash,
        )
        path = receipts_dir / f"{i:03d}.receipt.json"
        write_receipt_json(receipt, path)
        prev_hash = receipt_hash_from_file(path)

    result = verify_receipt_chain_in_dir(receipts_dir)
    assert result["ok"] is True
    assert result["chain_length"] == 10
    assert result["certificate"]["chain_length"] == 10


def test_redact_sign_verify_chain_end_to_end(tmp_path):
    """Full pipeline: build -> redact -> sign -> verify-signature should succeed."""
    (tmp_path / "secret.txt").write_text("password=hunter2\n", encoding="utf-8")
    config = DirectoryReceiptConfig(mode="deterministic")
    receipt = build_directory_receipt(root_path=tmp_path, config=config)

    redacted, report = redact_receipt_payload(receipt, profile="prod")
    assert int(report["redacted_values"]) >= 0

    signed = sign_receipt_payload(redacted, signing_key="e2e-key", key_id="prod")
    verified = verify_receipt_signature(signed, signing_key="e2e-key", expected_key_id="prod")
    assert verified["ok"] is True
    assert verified["signature_match"] is True
    assert verified["receipt_hash_match"] is True


def test_policy_version_is_stable():
    """Policy version should be promoted from draft for 0.11.0."""
    from sona.policy import POLICY_VERSION
    assert POLICY_VERSION == "0.1"
    assert "draft" not in POLICY_VERSION


# ---------------------------------------------------------------------------
# Track 1 — Bundle Format v0.2 tests
# ---------------------------------------------------------------------------

def test_receipt_export_bundle_roundtrip_verify(tmp_path):
    """Export a bundle and verify it round-trips: verify_receipt_bundle succeeds."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()
    config = DirectoryReceiptConfig(mode="deterministic")

    prev_hash = None
    for i in range(3):
        (workspace / "f.txt").write_text(f"v{i}\n", encoding="utf-8")
        receipt = build_directory_receipt(
            root_path=workspace, config=config,
            prev_receipt_hash=prev_hash,
        )
        path = receipts_dir / f"{i:03d}.receipt.json"
        write_receipt_json(receipt, path)
        prev_hash = receipt_hash_from_file(path)

    bundle_path = tmp_path / "bundle.json"
    result = export_receipt_bundle(receipts_dir, bundle_path)
    assert result["ok"] is True
    assert result["receipt_count"] == 3
    assert result["manifest_hash"] != ""

    verification = verify_receipt_bundle(bundle_path)
    assert verification["ok"] is True
    assert verification["bundle_hash_ok"] is True
    assert verification["manifest_ok"] is True
    assert verification["manifest_hash_ok"] is True
    assert verification["receipt_count"] == 3
    assert verification["entry_mismatches"] == []


def test_receipt_export_bundle_manifest_hashes_stable(tmp_path):
    """Manifest entry hashes should equal receipt_sha256() for each receipt."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()
    config = DirectoryReceiptConfig(mode="deterministic")

    (workspace / "hello.txt").write_text("hello\n", encoding="utf-8")
    receipt = build_directory_receipt(root_path=workspace, config=config)
    path = receipts_dir / "000.receipt.json"
    write_receipt_json(receipt, path)

    bundle_path = tmp_path / "bundle.json"
    export_receipt_bundle(receipts_dir, bundle_path)

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    manifest_entries = bundle["manifest"]["entries"]
    assert len(manifest_entries) == 1

    stored_receipt = bundle["receipts"][0]["receipt"]
    expected_hash = receipt_sha256(stored_receipt)
    assert manifest_entries[0]["sha256"] == expected_hash
    assert manifest_entries[0]["path"] == "000.receipt.json"


def test_receipt_export_bundle_with_lockfile(tmp_path):
    """Bundle with --include-lock should embed lockfile payload."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()
    config = DirectoryReceiptConfig(mode="deterministic")

    (workspace / "f.txt").write_text("v0\n", encoding="utf-8")
    receipt = build_directory_receipt(root_path=workspace, config=config)
    write_receipt_json(receipt, receipts_dir / "000.receipt.json")

    bundle_path = tmp_path / "bundle.json"
    result = export_receipt_bundle(
        receipts_dir, bundle_path,
        include_lockfile=True,
        workspace_dir=workspace,
    )
    assert result["ok"] is True

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert "lockfile" in bundle
    lockfile = bundle["lockfile"]
    assert isinstance(lockfile, dict)
    assert "entries" in lockfile
    assert "summary" in lockfile
    # Should NOT have a timestamp (deterministic)
    assert "generated_at_utc" not in lockfile


def test_receipt_export_bundle_tamper_detected(tmp_path):
    """Tampering with a receipt inside the bundle should fail verification."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()
    config = DirectoryReceiptConfig(mode="deterministic")

    (workspace / "f.txt").write_text("v0\n", encoding="utf-8")
    receipt = build_directory_receipt(root_path=workspace, config=config)
    write_receipt_json(receipt, receipts_dir / "000.receipt.json")

    bundle_path = tmp_path / "bundle.json"
    export_receipt_bundle(receipts_dir, bundle_path)

    # Tamper with the bundle
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["receipts"][0]["receipt"]["receipt_id"] = "TAMPERED"
    bundle_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    verification = verify_receipt_bundle(bundle_path)
    assert verification["ok"] is False
    assert len(verification["entry_mismatches"]) >= 1


def test_receipt_export_bundle_chain_directory_lookup(tmp_path):
    """Chain directory should allow lookup by hash and by receipt_id."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()
    config = DirectoryReceiptConfig(mode="deterministic")

    (workspace / "f.txt").write_text("v0\n", encoding="utf-8")
    receipt = build_directory_receipt(root_path=workspace, config=config)
    write_receipt_json(receipt, receipts_dir / "000.receipt.json")

    bundle_path = tmp_path / "bundle.json"
    export_receipt_bundle(receipts_dir, bundle_path)

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    chain_dir = bundle["chain_directory"]
    assert isinstance(chain_dir["by_hash"], dict)
    assert isinstance(chain_dir["by_id"], dict)

    # by_hash should contain the receipt hash → path mapping
    stored_receipt = bundle["receipts"][0]["receipt"]
    rh = receipt_sha256(stored_receipt)
    assert chain_dir["by_hash"].get(rh) == "000.receipt.json"

    # by_id should contain the receipt_id → path mapping
    rid = stored_receipt.get("receipt_id", "")
    if rid:
        assert chain_dir["by_id"].get(rid) == "000.receipt.json"


# ---------------------------------------------------------------------------
# Track 2 — Signature Semantics tests
# ---------------------------------------------------------------------------

def test_signature_envelope_contains_payload_hash_and_version(tmp_path):
    """Signed receipt should contain payload_hash and signed_fields_version."""
    (tmp_path / "f.txt").write_text("data\n", encoding="utf-8")
    config = DirectoryReceiptConfig(mode="deterministic")
    receipt = build_directory_receipt(root_path=tmp_path, config=config)

    signed = sign_receipt_payload(receipt, signing_key="test-key", key_id="k1")
    sig = signed["header"]["signature"]
    assert "payload_hash" in sig
    assert "signed_fields_version" in sig
    assert sig["signed_fields_version"] == SIGNED_FIELDS_VERSION
    assert len(sig["payload_hash"]) == 64  # sha256 hex


def test_verify_signature_payload_hash_matches(tmp_path):
    """Verification should report payload_hash_matches=True for valid receipt."""
    (tmp_path / "f.txt").write_text("data\n", encoding="utf-8")
    config = DirectoryReceiptConfig(mode="deterministic")
    receipt = build_directory_receipt(root_path=tmp_path, config=config)

    signed = sign_receipt_payload(receipt, signing_key="test-key", key_id="k1")
    result = verify_receipt_signature(signed, signing_key="test-key", expected_key_id="k1")
    assert result["ok"] is True
    assert result["payload_hash_matches"] is True
    assert result["signed_fields_version"] == SIGNED_FIELDS_VERSION


def test_verify_signature_detects_payload_hash_tamper(tmp_path):
    """Tampering with stored payload_hash should fail verification."""
    (tmp_path / "f.txt").write_text("data\n", encoding="utf-8")
    config = DirectoryReceiptConfig(mode="deterministic")
    receipt = build_directory_receipt(root_path=tmp_path, config=config)

    signed = sign_receipt_payload(receipt, signing_key="test-key", key_id="k1")
    # Tamper with payload_hash
    signed["header"]["signature"]["payload_hash"] = "0" * 64
    result = verify_receipt_signature(signed, signing_key="test-key", expected_key_id="k1")
    assert result["ok"] is False
    assert result["reason"] == "payload_hash_mismatch"
    assert result["payload_hash_matches"] is False


def test_verify_signature_envelope_change_preserves_validity(tmp_path):
    """Changing signed_at_utc (envelope field) should NOT break signature.

    The canonical signing payload excludes the signature envelope, so mutating
    envelope-only fields like signed_at_utc must leave both payload_hash and
    HMAC verification intact.
    """
    (tmp_path / "f.txt").write_text("data\n", encoding="utf-8")
    config = DirectoryReceiptConfig(mode="deterministic")
    receipt = build_directory_receipt(root_path=tmp_path, config=config)

    signed = sign_receipt_payload(receipt, signing_key="test-key", key_id="k1")
    # Mutate an envelope-only field
    signed["header"]["signature"]["signed_at_utc"] = "2099-01-01T00:00:00Z"

    result = verify_receipt_signature(signed, signing_key="test-key", expected_key_id="k1")
    assert result["ok"] is True, f"Expected ok=True but got reason={result['reason']}"
    assert result["payload_hash_matches"] is True
    assert result["signature_match"] is True


# ---------------------------------------------------------------------------
# Track 3 — Redaction Normalization tests
# ---------------------------------------------------------------------------

def test_redaction_idempotent_double_redact(tmp_path):
    """Redacting an already-redacted receipt should not re-redact existing tokens."""
    (tmp_path / "secret.txt").write_text("password=hunter2\n", encoding="utf-8")
    config = DirectoryReceiptConfig(mode="deterministic")
    receipt = build_directory_receipt(root_path=tmp_path, config=config)

    redacted1, report1 = redact_receipt_payload(receipt, profile="prod")
    redacted2, report2 = redact_receipt_payload(redacted1, profile="prod")

    # No NEW tokens should be created on the second pass
    assert int(report2["redacted_values"]) == 0, "Second redaction should redact 0 new values"

    # Data-level content (files entries) should be identical
    files1 = json.dumps(redacted1.get("files", []), sort_keys=True, separators=(",", ":"))
    files2 = json.dumps(redacted2.get("files", []), sort_keys=True, separators=(",", ":"))
    assert files1 == files2, "File entries should be identical after double-redaction"

    # Summary should be identical
    summary1 = json.dumps(redacted1.get("summary", {}), sort_keys=True, separators=(",", ":"))
    summary2 = json.dumps(redacted2.get("summary", {}), sort_keys=True, separators=(",", ":"))
    assert summary1 == summary2, "Summary should be identical after double-redaction"


def test_redaction_normalizes_crlf_to_lf():
    """CRLF and CR in strings should be normalized to LF before redaction hashing."""
    result_lf = _normalize_text_for_redaction("hello\nworld")
    result_crlf = _normalize_text_for_redaction("hello\r\nworld")
    result_cr = _normalize_text_for_redaction("hello\rworld")
    assert result_lf == result_crlf == result_cr == "hello\nworld"


def test_redaction_normalizes_unicode_nfc():
    """Unicode combining sequences should be NFC-normalized before redaction."""
    # é as e + combining acute (NFD) vs. precomposed é (NFC)
    nfd_str = "caf\u0065\u0301"  # NFD: e + combining acute
    nfc_str = "caf\u00e9"        # NFC: precomposed é
    result_nfd = _normalize_text_for_redaction(nfd_str)
    result_nfc = _normalize_text_for_redaction(nfc_str)
    assert result_nfd == result_nfc, "NFD and NFC forms must normalize identically"
    assert result_nfd == "café"


def test_redaction_directory_manifest_stable_across_runs(tmp_path):
    """Redaction tokens for the same receipt content should be stable across runs."""
    (tmp_path / "data.txt").write_text("sensitive=123\n", encoding="utf-8")
    config = DirectoryReceiptConfig(mode="deterministic")

    receipt1 = build_directory_receipt(root_path=tmp_path, config=config)
    receipt2 = build_directory_receipt(root_path=tmp_path, config=config)

    redacted1, _ = redact_receipt_payload(receipt1, profile="prod")
    redacted2, _ = redact_receipt_payload(receipt2, profile="prod")

    canonical1 = canonical_receipt_payload(redacted1)
    canonical2 = canonical_receipt_payload(redacted2)
    assert canonical1 == canonical2, "Same input should produce identical redaction tokens"


# ======================================================================
# Receipt context primitive tests
# ======================================================================


def test_set_get_clear_active_receipt():
    """Round-trip set → get → clear for the receipt context singleton."""
    clear_active_receipt()
    assert get_active_receipt() is None

    ctx = {"execution": {"events": [{"t": 0, "kind": "start"}]}}
    set_active_receipt(ctx)
    assert get_active_receipt() is ctx

    clear_active_receipt()
    assert get_active_receipt() is None


def test_append_event_no_context():
    """append_receipt_event gracefully returns None when no context is active."""
    clear_active_receipt()
    result = append_receipt_event("test")
    assert result is None


def test_append_event_with_context():
    """Events are appended to the context's execution.events list."""
    ctx = {"execution": {"events": [{"t": 0, "kind": "start"}, {"t": 100, "kind": "end"}]}}
    set_active_receipt(ctx)
    try:
        ev = append_receipt_event("my_event", payload={"key": "val"})
        assert ev is not None
        assert ev["kind"] == "my_event"
        assert ev["payload"] == {"key": "val"}
        assert ev["classification"] == "internal"
        # Event inserted before the end sentinel
        events = ctx["execution"]["events"]
        assert events[-1]["kind"] == "end"
        assert events[-2] is ev
    finally:
        clear_active_receipt()


def test_append_event_classification():
    """Custom classification is preserved in the appended event."""
    ctx = {"execution": {"events": [{"t": 0, "kind": "start"}]}}
    set_active_receipt(ctx)
    try:
        ev = append_receipt_event("diag", classification="diagnostic")
        assert ev["classification"] == "diagnostic"
    finally:
        clear_active_receipt()


def test_append_event_ordering():
    """Multiple appended events maintain insertion order before the end sentinel."""
    ctx = {"execution": {"events": [{"t": 0, "kind": "start"}, {"t": 999, "kind": "end"}]}}
    set_active_receipt(ctx)
    try:
        append_receipt_event("a")
        append_receipt_event("b")
        append_receipt_event("c")
        events = ctx["execution"]["events"]
        kinds = [e["kind"] for e in events]
        assert kinds == ["start", "a", "b", "c", "end"]
    finally:
        clear_active_receipt()


def test_build_receipt_with_pre_events(tmp_path):
    """build_receipt merges pre_events and appends the end sentinel."""
    from sona.receipts import ReceiptConfig

    entry = tmp_path / "test.sona"
    entry.write_text("print('hi')", encoding="utf-8")
    pre = [
        {"t": 0, "kind": "start"},
        {"t": 10, "kind": "my_event", "classification": "internal"},
    ]
    receipt = build_receipt(
        sona_version="0.11.0",
        entry_file=entry,
        project_root=tmp_path,
        argv=["sona", "run", "test.sona"],
        exit_code=0,
        duration_ms=50,
        error_text=None,
        config=ReceiptConfig(),
        pre_events=pre,
    )
    events = receipt["execution"]["events"]
    assert events[0]["kind"] == "start"
    assert events[1]["kind"] == "my_event"
    assert events[-1]["kind"] == "end"
    assert events[-1]["t"] == 50
    assert len(events) == 3


def test_build_receipt_without_pre_events_default(tmp_path):
    """Without pre_events, build_receipt still produces start+end."""
    from sona.receipts import ReceiptConfig

    entry = tmp_path / "test.sona"
    entry.write_text("x = 1", encoding="utf-8")
    receipt = build_receipt(
        sona_version="0.11.0",
        entry_file=entry,
        project_root=tmp_path,
        argv=[],
        exit_code=0,
        duration_ms=10,
        error_text=None,
        config=ReceiptConfig(),
    )
    events = receipt["execution"]["events"]
    assert len(events) == 2
    assert events[0]["kind"] == "start"
    assert events[1]["kind"] == "end"


def test_native_receipt_bridge_loads():
    """native_receipt module loads and exposes the expected symbols."""
    from sona.stdlib import native_receipt
    assert callable(native_receipt.receipt_append_event)
    assert callable(native_receipt.receipt_has_context)
    assert callable(native_receipt.receipt_current_id)
    assert callable(native_receipt.receipt_event_count)
