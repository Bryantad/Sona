import re
import sys
from pathlib import Path

from sona.stdlib_manifest import smod_path_for

sys.path.append(str(Path(__file__).resolve().parent))

from _surface_015 import PUBLIC_015_SURFACES, PUBLIC_DOCS, ROOT  # noqa: E402


PUBLIC_PLACEHOLDER_PATTERNS = [
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bFIXME\b", re.IGNORECASE),
    re.compile(r"NotImplemented", re.IGNORECASE),
    re.compile(r"\bpass\b", re.IGNORECASE),
    re.compile(r"\bstub\b", re.IGNORECASE),
    re.compile(r"placeholder", re.IGNORECASE),
    re.compile(r"coming soon", re.IGNORECASE),
    re.compile(r"not yet implemented", re.IGNORECASE),
    re.compile(r"fake success", re.IGNORECASE),
    re.compile(r"hardcoded demo", re.IGNORECASE),
]

OVERCLAIMS = [
    "Sona is now independent from Python",
    "Sona has a native LLVM compiler",
    "Sona now creates standalone binaries",
    "Sona has a completed package registry",
    "Sona has production-ready LSP completion",
    "Sona has production-ready debugger support",
    "Sona has native memory management",
]


def test_015_public_smod_files_have_no_placeholder_api_markers():
    failures = []
    for name in sorted(PUBLIC_015_SURFACES):
        path = smod_path_for(name)
        text = path.read_text(encoding="utf-8")
        for pattern in PUBLIC_PLACEHOLDER_PATTERNS:
            if pattern.search(text):
                failures.append(f"{path.relative_to(ROOT)} matched {pattern.pattern}")
    assert failures == []


def test_015_user_facing_docs_do_not_overclaim_or_mark_public_apis_placeholder_only():
    docs = [
        ROOT / "README.md",
        ROOT / "CHANGELOG.md",
        ROOT / "RELEASE_NOTES_v0.15.0.md",
        *PUBLIC_DOCS.values(),
        ROOT / "docs" / "release" / "0.15.0-handoff-report.md",
        ROOT / "docs" / "release" / "0.15.0-module-matrix.md",
        ROOT / "docs" / "release" / "0.15.0-validation-ledger.md",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in docs if path.exists())

    for claim in OVERCLAIMS:
        assert claim not in combined
    for phrase in ["placeholder-only", "fake success", "coming soon", "not yet implemented"]:
        assert phrase not in combined.lower()
