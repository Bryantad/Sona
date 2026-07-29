from __future__ import annotations

import json
from pathlib import Path

from sona.receipts import ReceiptConfig, build_receipt, write_receipt_json


def test_legacy_run_receipt_is_schema_one_redacted_hashed_and_deterministic(tmp_path: Path, monkeypatch):
    entry = tmp_path / "main.sona"
    entry.write_text('print("hello")\n', encoding="utf-8")
    monkeypatch.setenv("SONA_API_KEY", "top-secret")
    receipt = build_receipt(
        sona_version="0.15.2", entry_file=entry, project_root=tmp_path,
        argv=["sona", "run", "main.sona"], exit_code=1, duration_ms=7,
        error_text="token=also-secret", config=ReceiptConfig(env_allowlist=("SONA_API_KEY",)),
        timestamp_utc="2026-01-01T00:00:00Z",
    )
    assert receipt["schema_version"] == 1
    assert receipt["receipt_version"] == "1"
    assert receipt["timestamp_utc"] == "2026-01-01T00:00:00Z"
    rendered = json.dumps(receipt)
    assert "top-secret" not in rendered
    assert "also-secret" not in rendered
    assert receipt["policy_hash"]
    assert receipt["receipt_hash"].startswith("sha256:")
    assert receipt["execution"]["exit_code"] == 1, "legacy run fields remain available"

    path = tmp_path / "receipt.json"
    receipt["execution"]["events"].insert(-1, {"kind": "test", "t": 1})
    old_hash = receipt["receipt_hash"]
    write_receipt_json(receipt, path)
    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["receipt_hash"] != old_hash
