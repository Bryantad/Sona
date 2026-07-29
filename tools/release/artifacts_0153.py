#!/usr/bin/env python3
"""Build and inspect reproducible Sona 0.15.3 custom archives."""

from __future__ import annotations

import argparse
import fnmatch
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
import tarfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


VERSION = "0.15.3"
SOURCE_PREFIX = f"sona-{VERSION}"
SOURCE_EXCLUSIONS = {
    "RELEASE_NOTES_v0.15.0.md",
    "RELEASE_NOTES_v0.15.1.md",
    "RELEASE_NOTES_v0.15.2.md",
}
FORBIDDEN_SEGMENTS = {
    ".git",
    ".release-artifacts",
    "__pycache__",
    "node_modules",
    "target",
    "dist",
    "build",
    "coverage",
}
REQUIRED_SOURCE_PATHS = {
    "docs/release/0.15.3-source-manifest.json",
    "native/Cargo.lock",
    "native/Cargo.toml",
    "rust-toolchain.toml",
    "spec/bytecode.md",
    "spec/syntax-grammar.md",
    "tests/release/run_0153_release_gate.py",
    "tests/release/native-scratch.Dockerfile",
    "tests/release/cases/negative_legacy_fn.expected.json",
    "tests/conformance/run_0153_differential_conformance.py",
    "tests/conformance/diagnostics/legacy_fn.expected.json",
    "RELEASE_NOTES_v0.15.3.md",
    "docs/release/0.15.3-implementation-report.md",
    "pyproject.toml",
    "tools/release/import_0153_manifest.py",
    "tools/release/artifacts_0153.py",
    "tools/release/certify_0153.py",
    "tools/release/finalize_0153_release.py",
    "tools/release/promote_0153.py",
    "tools/release/publish_0153.py",
    "vscode-extension/package-lock.json",
}


def _git(root: Path, *arguments: str, text: bool = True) -> str | bytes:
    process = subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        text=text,
        shell=False,
        check=True,
    )
    return process.stdout


def source_epoch(root: Path, commit: str) -> int:
    return int(str(_git(root, "show", "-s", "--format=%ct", commit)).strip())


def _tree(root: Path, commit: str) -> list[tuple[str, int, bytes]]:
    raw = _git(root, "ls-tree", "-r", "-z", "--full-tree", commit, text=False)
    assert isinstance(raw, bytes)
    records = []
    for item in raw.split(b"\0"):
        if not item:
            continue
        metadata, encoded_path = item.split(b"\t", 1)
        mode, object_type, _object_id = metadata.decode("ascii").split()
        if object_type != "blob":
            continue
        path = encoded_path.decode("utf-8", "surrogateescape").replace("\\", "/")
        content = _git(root, "show", f"{commit}:{path}", text=False)
        assert isinstance(content, bytes)
        records.append((path, int(mode, 8), content))
    return sorted(records, key=lambda item: item[0])


def _matches_pattern(path: str, pattern: str) -> bool:
    normalized = pattern.replace("\\", "/")
    if normalized.endswith("/**"):
        prefix = normalized[:-3]
        return path == prefix or path.startswith(f"{prefix}/")
    if normalized.startswith("**/"):
        return fnmatch.fnmatchcase(path, normalized[3:]) or fnmatch.fnmatchcase(
            path, normalized
        )
    return fnmatch.fnmatchcase(path, normalized)


def _source_allowed(path: str, manifest_exclusions: list[str] | None = None) -> bool:
    pure = PurePosixPath(path)
    if manifest_exclusions and any(
        _matches_pattern(path, pattern) for pattern in manifest_exclusions
    ):
        return False
    if path in SOURCE_EXCLUSIONS:
        return False
    if path.startswith("extensions/") or path.startswith(".release-artifacts/"):
        return False
    if path.startswith("docs/release-notes/"):
        return False
    if path.endswith(".map") or path.endswith(".pyc"):
        return False
    if ".env" in pure.parts:
        return False
    if any(part in FORBIDDEN_SEGMENTS for part in pure.parts):
        return False
    return True


def build_source_archive(
    repository: Path,
    commit: str,
    destination: Path,
) -> dict[str, Any]:
    repository = repository.resolve(strict=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    epoch = source_epoch(repository, commit)
    complete_tree = _tree(repository, commit)
    manifest_path = "docs/release/0.15.3-source-manifest.json"
    manifest_record = next(
        (content for path, _mode, content in complete_tree if path == manifest_path),
        None,
    )
    if manifest_record is None:
        raise ValueError("source archive is missing the reviewed source manifest")
    manifest = json.loads(manifest_record.decode("utf-8"))
    if manifest.get("schema_id") != "sona.source-import-manifest.schema-1":
        raise ValueError("source archive manifest has the wrong schema")
    manifest_exclusions = manifest.get("excluded_paths", [])
    if not isinstance(manifest_exclusions, list) or not all(
        isinstance(pattern, str) for pattern in manifest_exclusions
    ):
        raise ValueError("source archive manifest exclusions are invalid")
    records = [
        record
        for record in complete_tree
        if _source_allowed(record[0], manifest_exclusions)
    ]
    paths = {path for path, _mode, _content in records}
    missing = REQUIRED_SOURCE_PATHS - paths
    if missing:
        raise ValueError(f"source archive is missing required paths: {sorted(missing)}")

    with destination.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=epoch) as compressed:
            with tarfile.open(
                fileobj=compressed,
                mode="w",
                format=tarfile.PAX_FORMAT,
            ) as archive:
                for path, mode, content in records:
                    info = tarfile.TarInfo(f"{SOURCE_PREFIX}/{path}")
                    info.size = len(content)
                    info.mtime = epoch
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    info.mode = 0o755 if mode & 0o111 else 0o644
                    archive.addfile(info, io.BytesIO(content))
    return inspect_archive(destination, kind="source")


def _zip_datetime(epoch: int) -> tuple[int, int, int, int, int, int]:
    import datetime

    value = datetime.datetime.fromtimestamp(max(epoch, 315532800), datetime.timezone.utc)
    return (value.year, value.month, value.day, value.hour, value.minute, value.second // 2 * 2)


def build_native_archive(
    binary: Path,
    destination: Path,
    *,
    archive_kind: str,
    epoch: int,
) -> dict[str, Any]:
    binary = binary.resolve(strict=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if archive_kind == "windows":
        info = zipfile.ZipInfo("sona.exe", _zip_datetime(epoch))
        info.create_system = 3
        info.external_attr = 0o755 << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        with zipfile.ZipFile(destination, "w") as archive:
            archive.writestr(info, binary.read_bytes())
    elif archive_kind == "linux":
        with destination.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=epoch) as compressed:
                with tarfile.open(
                    fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT
                ) as archive:
                    content = binary.read_bytes()
                    info = tarfile.TarInfo("sona")
                    info.size = len(content)
                    info.mtime = epoch
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    info.mode = 0o755
                    archive.addfile(info, io.BytesIO(content))
    else:
        raise ValueError(f"unsupported native archive kind: {archive_kind}")
    return inspect_archive(destination, kind="native")


def _members(path: Path) -> list[tuple[str, bytes | None, str]]:
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            return [
                (
                    info.filename.replace("\\", "/"),
                    None if info.is_dir() else archive.read(info),
                    "file" if not info.is_dir() else "directory",
                )
                for info in archive.infolist()
            ]
    with tarfile.open(path, "r:*") as archive:
        members = []
        for info in archive.getmembers():
            content = None
            if info.isfile():
                stream = archive.extractfile(info)
                content = stream.read() if stream is not None else b""
            kind = (
                "file"
                if info.isfile()
                else "directory"
                if info.isdir()
                else "link"
                if info.issym() or info.islnk()
                else "special"
            )
            members.append((info.name.replace("\\", "/"), content, kind))
        return members


def _safe_member(name: str) -> PurePosixPath:
    pure = PurePosixPath(name)
    if (
        pure.is_absolute()
        or not pure.parts
        or any(part in {"", ".", ".."} for part in pure.parts)
        or "\\" in name
    ):
        raise ValueError(f"unsafe archive member: {name}")
    return pure


def _version_tuple(value: str) -> tuple[int, ...]:
    numbers = []
    for part in value.split("."):
        digits = "".join(character for character in part if character.isdigit())
        numbers.append(int(digits or 0))
    return tuple(numbers)


def inspect_archive(path: Path, *, kind: str) -> dict[str, Any]:
    path = path.resolve(strict=True)
    members = _members(path)
    names: set[str] = set()
    payloads: dict[str, bytes] = {}
    for name, content, member_kind in members:
        pure = _safe_member(name)
        if name in names:
            raise ValueError(f"duplicate archive member: {name}")
        names.add(name)
        if member_kind in {"link", "special"}:
            raise ValueError(f"unsafe archive member type: {name}")
        if content is not None:
            payloads[name] = content
        relative_parts = pure.parts[1:] if kind == "source" else pure.parts
        if kind in {"source", "native", "python"}:
            if any(part in FORBIDDEN_SEGMENTS for part in relative_parts):
                raise ValueError(f"forbidden archive path: {name}")
            if any(
                part == ".env"
                or part.startswith(".env.")
                or part.endswith(".pyc")
                for part in relative_parts
            ):
                raise ValueError(f"forbidden archive path: {name}")
            if name.endswith(".map"):
                raise ValueError(f"forbidden source map: {name}")
            lowered_parts = tuple(part.lower() for part in relative_parts)
            if any(
                part in {"__macosx", ".ds_store", "thumbs.db"}
                or part.endswith("~")
                for part in lowered_parts
            ):
                raise ValueError(f"forbidden temporary metadata: {name}")
            if (
                ".github" in lowered_parts
                and any(
                    token in part
                    for part in lowered_parts
                    for token in ("credential", "secret", "token", ".pem", ".key")
                )
            ):
                raise ValueError(f"forbidden credential-like archive path: {name}")
        if kind == "source":
            relative = "/".join(relative_parts)
            if not _source_allowed(relative):
                raise ValueError(f"excluded source archive path: {name}")
        if kind == "vsix":
            lowered = name.lower()
            if (
                lowered.endswith(".map")
                or lowered.startswith("extension/src/")
                or lowered.endswith(".ts")
                or "/native/target/" in lowered
                or "/.release-artifacts/" in lowered
                or "/extensions/" in lowered
            ):
                raise ValueError(f"forbidden VSIX content: {name}")

    if kind == "source":
        manifest_name = (
            f"{SOURCE_PREFIX}/docs/release/0.15.3-source-manifest.json"
        )
        if manifest_name not in payloads:
            raise ValueError("source archive is missing its reviewed source manifest")
        manifest = json.loads(payloads[manifest_name].decode("utf-8"))
        exclusions = manifest.get("excluded_paths", [])
        relative_names = {
            "/".join(PurePosixPath(name).parts[1:])
            for name in names
            if len(PurePosixPath(name).parts) > 1
        }
        missing = REQUIRED_SOURCE_PATHS - relative_names
        if missing:
            raise ValueError(f"source archive is missing required content: {sorted(missing)}")
        forbidden = sorted(
            relative
            for relative in relative_names
            if any(_matches_pattern(relative, pattern) for pattern in exclusions)
        )
        if forbidden:
            raise ValueError(f"source archive contains manifest exclusions: {forbidden}")
        secret_patterns = (
            re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
            re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
            re.compile(rb"\bghp_[A-Za-z0-9]{30,}\b"),
            re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{30,}\b"),
            re.compile(rb"\bsk-[A-Za-z0-9]{24,}\b"),
        )
        for name, content in payloads.items():
            if any(pattern.search(content) for pattern in secret_patterns):
                raise ValueError(f"credential-like content in source archive: {name}")
    if kind == "vsix":
        package_name = "extension/package.json"
        if package_name not in payloads:
            raise ValueError("VSIX is missing extension/package.json")
        package = json.loads(payloads[package_name].decode("utf-8"))
        for dependency in package.get("devDependencies", {}):
            prefix = f"extension/node_modules/{dependency}/"
            if any(name.startswith(prefix) for name in names):
                raise ValueError(f"VSIX includes development dependency: {dependency}")
        minimums = {
            "minimatch": (10, 2, 5),
            "brace-expansion": (5, 0, 8),
        }
        for package_path, content in payloads.items():
            if not package_path.endswith("/package.json"):
                continue
            package_metadata = json.loads(content.decode("utf-8"))
            dependency = package_metadata.get("name")
            if dependency in minimums:
                version = package_metadata.get("version", "0")
                if _version_tuple(version) < minimums[dependency]:
                    raise ValueError(
                        f"VSIX includes vulnerable {dependency} version {version}"
                    )
    if kind in {"source", "native"}:
        _validate_custom_archive_metadata(path, members, kind)
    return {
        "status": "pass",
        "kind": kind,
        "filename": path.name,
        "members": len(members),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
        "bytes": path.stat().st_size,
    }


def _validate_custom_archive_metadata(
    path: Path,
    members: list[tuple[str, bytes | None, str]],
    kind: str,
) -> None:
    names = [name for name, _content, _member_kind in members]
    if names != sorted(names):
        raise ValueError("custom archive members are not sorted")
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            timestamps = {info.date_time for info in archive.infolist()}
            if len(timestamps) != 1:
                raise ValueError("custom ZIP timestamps are not normalized")
            for info in archive.infolist():
                mode = info.external_attr >> 16 & 0o777
                if not info.is_dir() and mode != 0o755:
                    raise ValueError(f"custom ZIP mode is not normalized: {info.filename}")
        return
    with tarfile.open(path, "r:*") as archive:
        timestamps = {member.mtime for member in archive.getmembers()}
        if len(timestamps) != 1:
            raise ValueError("custom tar timestamps are not normalized")
        for member in archive.getmembers():
            if member.uid != 0 or member.gid != 0 or member.uname or member.gname:
                raise ValueError(f"custom tar ownership is not normalized: {member.name}")
            expected_mode = 0o755 if kind == "native" else (
                0o755 if member.mode & 0o111 else 0o644
            )
            if member.mode != expected_mode:
                raise ValueError(f"custom tar mode is not normalized: {member.name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    source = subparsers.add_parser("source")
    source.add_argument("--repository", type=Path, required=True)
    source.add_argument("--commit", required=True)
    source.add_argument("--output", type=Path, required=True)
    native = subparsers.add_parser("native")
    native.add_argument("--binary", type=Path, required=True)
    native.add_argument("--output", type=Path, required=True)
    native.add_argument("--kind", choices=["windows", "linux"], required=True)
    native.add_argument("--epoch", type=int, required=True)
    inspect = subparsers.add_parser("inspect")
    inspect.add_argument("--archive", type=Path, required=True)
    inspect.add_argument(
        "--kind", choices=["source", "native", "python", "vsix"], required=True
    )
    args = parser.parse_args(argv)
    if args.command == "source":
        result = build_source_archive(args.repository, args.commit, args.output)
    elif args.command == "native":
        result = build_native_archive(
            args.binary,
            args.output,
            archive_kind=args.kind,
            epoch=args.epoch,
        )
    else:
        result = inspect_archive(args.archive, kind=args.kind)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
