from __future__ import annotations

import json
import re
from pathlib import Path

from tools.release.finalize_0153_release import (
    PUBLISHED_FILES,
    render_markdown,
    verify_sha256sums,
    write_sha256sums,
)


def test_checksum_authority_covers_exact_assets_except_itself(tmp_path: Path) -> None:
    for filename in sorted(PUBLISHED_FILES - {"SHA256SUMS"}):
        (tmp_path / filename).write_bytes(f"{filename}\n".encode("utf-8"))

    checksum = write_sha256sums(tmp_path)
    verify_sha256sums(tmp_path)

    lines = checksum.read_text(encoding="ascii").splitlines()
    assert len(lines) == len(PUBLISHED_FILES) - 1
    assert not any(line.endswith("  SHA256SUMS") for line in lines)
    assert all(re.fullmatch(r"[0-9A-F]{64}  [^/\\]+", line) for line in lines)


def test_certification_markdown_is_deterministic_from_json() -> None:
    report = {
        "schema_id": "sona.release-certification.schema-1",
        "source_commit": "a" * 40,
        "generated_at_utc": "2026-07-27T12:00:00Z",
        "result": "pass",
        "certification_matrix": [
            {
                "host_os": "Linux",
                "architecture": "x86_64",
                "python": "3.12.0",
                "phases": ["native", "python"],
                "toolchains": {"rustc": "rustc 1.94.0"},
            }
        ],
        "artifacts": [
            {
                "filename": "sona.tar.gz",
                "byte_size": 42,
                "sha256": "A" * 64,
                "archive_inspection": "pass",
            }
        ],
    }
    round_tripped = json.loads(json.dumps(report, sort_keys=True))
    assert render_markdown(report) == render_markdown(round_tripped)
    assert "Native Core remains a preview" in render_markdown(report)
    assert "PyPI and VS Code Marketplace publication were not performed" in render_markdown(
        report
    )
