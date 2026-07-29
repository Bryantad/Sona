from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.release.finalize_0153_release import PUBLISHED_FILES, write_sha256sums
from tools.release.publish_0153 import validate_assets


def _assets(root: Path) -> None:
    for filename in sorted(PUBLISHED_FILES - {"SHA256SUMS"}):
        content = f"{filename}\n".encode("utf-8")
        if filename == "sona-0.15.3-certification.json":
            content = (
                json.dumps(
                    {
                        "schema_id": "sona.release-certification.schema-1",
                        "result": "pass",
                        "source_commit": "a" * 40,
                    }
                )
                + "\n"
            ).encode("utf-8")
        (root / filename).write_bytes(content)
    write_sha256sums(root)


def test_publication_requires_exact_hash_verified_asset_set(tmp_path: Path) -> None:
    _assets(tmp_path)
    validated = validate_assets(tmp_path)
    assert set(validated) == PUBLISHED_FILES

    (tmp_path / "sona-0.15.3-source.tar.gz").write_bytes(b"changed")
    with pytest.raises(RuntimeError, match="SHA-256 verification failed"):
        validate_assets(tmp_path)


def test_publication_rejects_missing_or_extra_asset(tmp_path: Path) -> None:
    _assets(tmp_path)
    (tmp_path / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    with pytest.raises(RuntimeError, match="asset set mismatch"):
        validate_assets(tmp_path)
