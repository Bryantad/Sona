from __future__ import annotations

import hashlib
import json
import subprocess
import tarfile
import zipfile
from pathlib import Path

import pytest

from tools.release.artifacts_0153 import (
    REQUIRED_SOURCE_PATHS,
    SOURCE_PREFIX,
    build_native_archive,
    build_source_archive,
    inspect_archive,
    source_epoch,
)


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
        shell=False,
    )
    return completed.stdout.strip()


def _repository(tmp_path: Path) -> tuple[Path, str]:
    repository = tmp_path / "repository"
    repository.mkdir()
    _git(repository, "init", "-q")
    _git(repository, "config", "user.name", "Release Test")
    _git(repository, "config", "user.email", "release-test@example.invalid")
    for relative in sorted(REQUIRED_SOURCE_PATHS):
        target = repository / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if relative == "docs/release/0.15.3-source-manifest.json":
            target.write_text(
                json.dumps(
                    {
                        "schema_id": "sona.source-import-manifest.schema-1",
                        "excluded_paths": [
                            "RELEASE_NOTES_v0.15.0.md",
                            "docs/release-notes/**",
                            "extensions/**",
                            "**/*.map",
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
                newline="\n",
            )
        else:
            target.write_text(f"{relative}\n", encoding="utf-8", newline="\n")
    excluded = {
        "RELEASE_NOTES_v0.15.0.md": "historical",
        "docs/release-notes/old.md": "historical",
        "extensions/companion.txt": "companion",
        "vscode-extension/out/extension.js.map": "map",
    }
    for relative, content in excluded.items():
        target = repository / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    _git(repository, "add", ".")
    _git(
        repository,
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-q",
        "-m",
        "fixture",
    )
    return repository, _git(repository, "rev-parse", "HEAD")


def test_source_archive_is_reproducible_normalized_and_filtered(tmp_path: Path) -> None:
    repository, commit = _repository(tmp_path)
    first = tmp_path / "first.tar.gz"
    second = tmp_path / "second.tar.gz"

    result = build_source_archive(repository, commit, first)
    build_source_archive(repository, commit, second)

    assert result["status"] == "pass"
    assert first.read_bytes() == second.read_bytes()
    epoch = source_epoch(repository, commit)
    with tarfile.open(first, "r:gz") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        assert names == sorted(names)
        assert all(name.startswith(f"{SOURCE_PREFIX}/") for name in names)
        assert all(member.uid == 0 and member.gid == 0 for member in members)
        assert all(member.mtime == epoch for member in members)
        assert not any("RELEASE_NOTES_v0.15.0.md" in name for name in names)
        assert not any("/docs/release-notes/" in name for name in names)
        assert not any("/extensions/" in name for name in names)
        assert not any(name.endswith(".map") for name in names)


@pytest.mark.parametrize("kind, suffix, member", [
    ("windows", ".zip", "sona.exe"),
    ("linux", ".tar.gz", "sona"),
])
def test_native_archives_are_reproducible_and_executable(
    tmp_path: Path,
    kind: str,
    suffix: str,
    member: str,
) -> None:
    binary = tmp_path / ("sona.exe" if kind == "windows" else "sona")
    binary.write_bytes(b"native-binary")
    first = tmp_path / f"first{suffix}"
    second = tmp_path / f"second{suffix}"

    build_native_archive(binary, first, archive_kind=kind, epoch=1_700_000_000)
    build_native_archive(binary, second, archive_kind=kind, epoch=1_700_000_000)

    assert hashlib.sha256(first.read_bytes()).digest() == hashlib.sha256(
        second.read_bytes()
    ).digest()
    if kind == "windows":
        with zipfile.ZipFile(first) as archive:
            info = archive.getinfo(member)
            assert info.external_attr >> 16 & 0o777 == 0o755
    else:
        with tarfile.open(first, "r:gz") as archive:
            info = archive.getmember(member)
            assert info.mode == 0o755
            assert info.uid == 0
            assert info.gid == 0


def test_archive_inspection_rejects_traversal_and_links(tmp_path: Path) -> None:
    traversal = tmp_path / "traversal.zip"
    with zipfile.ZipFile(traversal, "w") as archive:
        archive.writestr("../escape", b"bad")
    with pytest.raises(ValueError, match="unsafe archive member"):
        inspect_archive(traversal, kind="native")

    link = tmp_path / "link.tar"
    with tarfile.open(link, "w") as archive:
        info = tarfile.TarInfo("sona")
        info.type = tarfile.SYMTYPE
        info.linkname = "../../escape"
        archive.addfile(info)
    with pytest.raises(ValueError, match="unsafe archive member type"):
        inspect_archive(link, kind="native")


def test_vsix_inspection_rejects_source_and_vulnerable_dependencies(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.vsix"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr(
            "extension/package.json",
            json.dumps({"name": "sona", "devDependencies": {}}),
        )
        archive.writestr("extension/src/extension.ts", "export {};")
    with pytest.raises(ValueError, match="forbidden VSIX content"):
        inspect_archive(source, kind="vsix")

    vulnerable = tmp_path / "vulnerable.vsix"
    with zipfile.ZipFile(vulnerable, "w") as archive:
        archive.writestr(
            "extension/package.json",
            json.dumps({"name": "sona", "devDependencies": {}}),
        )
        archive.writestr(
            "extension/node_modules/minimatch/package.json",
            json.dumps({"name": "minimatch", "version": "10.2.4"}),
        )
    with pytest.raises(ValueError, match="vulnerable minimatch"):
        inspect_archive(vulnerable, kind="vsix")
