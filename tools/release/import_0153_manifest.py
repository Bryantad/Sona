#!/usr/bin/env python3
"""Create, apply, and verify the reviewed Sona 0.15.3 source manifest."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import platform
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_ID = "sona.source-import-manifest.schema-1"
BOOTSTRAP_PATHS = {
    "docs/release/0.15.3-source-manifest.json",
    "tools/release/import_0153_manifest.py",
}
DEFAULT_EXCLUSIONS = [
    ".release-artifacts/**",
    "**/__pycache__/**",
    "**/*.pyc",
    "**/.env",
    "**/.env.*",
    "**/node_modules/**",
    "**/target/**",
    "**/dist/**",
    "**/build/**",
    "**/coverage/**",
    "**/*.vsix",
    "extensions/**",
    "**/*.map",
    "RELEASE_NOTES_v0.15.0.md",
    "RELEASE_NOTES_v0.15.1.md",
    "RELEASE_NOTES_v0.15.2.md",
    "docs/release-notes/**",
]


def _git(root: Path, *arguments: str, text: bool = True) -> str | bytes:
    process = subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        text=text,
        shell=False,
        check=False,
    )
    if process.returncode != 0:
        stderr = process.stderr if text else process.stderr.decode("utf-8", "replace")
        raise RuntimeError(f"git {' '.join(arguments)} failed: {stderr.strip()}")
    return process.stdout


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest().upper()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _normal_path(value: str) -> str:
    if "\\" in value:
        raise ValueError(f"path must use POSIX separators: {value}")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"unsafe relative path: {value}")
    return path.as_posix()


def _resolve_confined(root: Path, relative: str, *, require_exists: bool) -> Path:
    relative = _normal_path(relative)
    candidate = root.joinpath(*PurePosixPath(relative).parts)
    resolved_root = root.resolve(strict=True)
    resolved = candidate.resolve(strict=require_exists)
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise ValueError(f"path escapes root: {relative}")
    probe = candidate
    while probe != root and probe.exists():
        metadata = probe.lstat()
        attributes = getattr(metadata, "st_file_attributes", 0)
        if stat.S_ISLNK(metadata.st_mode) or attributes & 0x400:
            raise ValueError(f"symlink or reparse-point path is forbidden: {relative}")
        probe = probe.parent
    return candidate


def _matches_exclusion(path: str, patterns: list[str]) -> bool:
    path = _normal_path(path)
    for pattern in patterns:
        normalized = pattern.replace("\\", "/")
        if normalized.endswith("/**") and (
            path == normalized[:-3] or path.startswith(normalized[:-2])
        ):
            return True
        if fnmatch.fnmatchcase(path, normalized):
            return True
        if normalized.startswith("**/") and fnmatch.fnmatchcase(
            path, normalized[3:]
        ):
            return True
    return False


def _release_area(path: str) -> str:
    if path.startswith("native/"):
        return "native"
    if path.startswith("tests/"):
        return "tests"
    if path.startswith("docs/") or path.startswith("spec/") or path.startswith(
        "RELEASE_NOTES_"
    ):
        return "docs"
    if path.startswith("vscode-extension/"):
        return "extension"
    if path.startswith(".github/") or path.startswith("scripts/") or path.startswith(
        "tools/"
    ) or path in {"pyproject.toml", "requirements.txt", ".gitignore", ".nvmrc", "rust-toolchain.toml"}:
        return "packaging"
    return "runtime"


def _reason(path: str, classification: str, area: str) -> str:
    if classification == "deleted":
        return f"Remove superseded {area} content as reviewed for Sona 0.15.3."
    return f"Include reviewed Sona 0.15.3 {area} implementation from {path}."


def _base_file(root: Path, base: str, path: str) -> bytes | None:
    process = subprocess.run(
        ["git", "show", f"{base}:{path}"],
        cwd=root,
        capture_output=True,
        shell=False,
        check=False,
    )
    return process.stdout if process.returncode == 0 else None


def _changed_paths(root: Path, base: str) -> dict[str, str]:
    raw = _git(root, "diff", "--name-status", "--no-renames", "-z", base, text=False)
    assert isinstance(raw, bytes)
    fields = raw.decode("utf-8", "surrogateescape").split("\0")
    changed: dict[str, str] = {}
    index = 0
    while index + 1 < len(fields) and fields[index]:
        status_code = fields[index]
        path = fields[index + 1]
        index += 2
        classification = {
            "A": "new",
            "M": "modified",
            "D": "deleted",
            "T": "modified",
        }.get(status_code[:1])
        if classification is None:
            raise ValueError(f"unsupported git status {status_code} for {path}")
        changed[path.replace("\\", "/")] = classification
    untracked = _git(
        root,
        "ls-files",
        "--others",
        "--exclude-standard",
        "-z",
        text=False,
    )
    assert isinstance(untracked, bytes)
    for path in untracked.decode("utf-8", "surrogateescape").split("\0"):
        if path:
            changed.setdefault(path.replace("\\", "/"), "new")
    return changed


def create_manifest(
    source_root: Path,
    destination_base: str,
    output: Path,
    summary_dir: Path,
) -> None:
    source_root = source_root.resolve(strict=True)
    resolved_base = str(
        _git(source_root, "rev-parse", "--verify", f"{destination_base}^{{commit}}")
    ).strip()
    if resolved_base != destination_base:
        raise ValueError(
            f"destination base must be a full commit SHA: {destination_base}"
        )
    exclusions = list(DEFAULT_EXCLUSIONS)
    entries = []
    excluded = []
    for path, classification in sorted(
        _changed_paths(source_root, destination_base).items()
    ):
        path = _normal_path(path)
        if path in BOOTSTRAP_PATHS:
            continue
        if _matches_exclusion(path, exclusions):
            excluded.append(path)
            continue
        area = _release_area(path)
        if classification == "deleted":
            content = _base_file(source_root, destination_base, path)
            if content is None:
                raise ValueError(f"deleted base file is missing: {path}")
            source_hash = _sha256_bytes(content)
            destination_hash = None
        else:
            source = _resolve_confined(source_root, path, require_exists=True)
            if not source.is_file():
                raise ValueError(f"manifest source is not a file: {path}")
            source_hash = _sha256_file(source)
            destination_hash = source_hash
        entries.append(
            {
                "source_relative_path": path,
                "destination_relative_path": path,
                "source_sha256": source_hash,
                "destination_sha256": destination_hash,
                "classification": classification,
                "release_area": area,
                "reason": _reason(path, classification, area),
            }
        )
    destination_keys = [entry["destination_relative_path"].casefold() for entry in entries]
    if len(destination_keys) != len(set(destination_keys)):
        raise ValueError("duplicate or case-colliding destination paths")
    manifest = {
        "schema_id": SCHEMA_ID,
        "schema": 1,
        "release_version": "0.15.3",
        "source_workspace_baseline": str(_git(source_root, "rev-parse", "HEAD")).strip(),
        "destination_base_commit": destination_base,
        "excluded_paths": exclusions,
        "entries": entries,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    _write_summary(
        summary_dir,
        "create",
        manifest,
        entries,
        excluded,
    )


def _load_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    required_top_level = {
        "schema_id",
        "schema",
        "release_version",
        "source_workspace_baseline",
        "destination_base_commit",
        "excluded_paths",
        "entries",
    }
    if set(manifest) != required_top_level:
        raise ValueError("source manifest top-level fields are not exact")
    if manifest.get("schema_id") != SCHEMA_ID or manifest.get("schema") != 1:
        raise ValueError("unsupported source manifest schema")
    if manifest.get("release_version") != "0.15.3":
        raise ValueError("source manifest release version is not 0.15.3")
    for field in ("source_workspace_baseline", "destination_base_commit"):
        value = manifest.get(field)
        if (
            not isinstance(value, str)
            or len(value) != 40
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise ValueError(f"source manifest {field} is not a full Git SHA")
    exclusions = manifest.get("excluded_paths")
    if not isinstance(exclusions, list) or not all(
        isinstance(pattern, str)
        and pattern
        and "\\" not in pattern
        and not pattern.startswith("/")
        and ".." not in PurePosixPath(pattern).parts
        for pattern in exclusions
    ):
        raise ValueError("source manifest exclusions are invalid")
    missing_exclusions = set(DEFAULT_EXCLUSIONS) - set(exclusions)
    if missing_exclusions:
        raise ValueError(
            f"source manifest is missing mandatory exclusions: "
            f"{sorted(missing_exclusions)}"
        )
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ValueError("manifest entries must be an array")
    required = {
        "source_relative_path",
        "destination_relative_path",
        "source_sha256",
        "destination_sha256",
        "classification",
        "release_area",
        "reason",
    }
    destinations: set[str] = set()
    for entry in entries:
        if set(entry) != required:
            raise ValueError("manifest entry fields are not exact")
        source = _normal_path(entry["source_relative_path"])
        destination = _normal_path(entry["destination_relative_path"])
        if destination.casefold() in destinations:
            raise ValueError(f"duplicate destination: {destination}")
        destinations.add(destination.casefold())
        if _matches_exclusion(destination, manifest["excluded_paths"]):
            raise ValueError(f"excluded destination is forbidden: {destination}")
        if entry["classification"] not in {"new", "modified", "deleted"}:
            raise ValueError(f"invalid classification: {destination}")
        if entry["release_area"] not in {
            "runtime",
            "tests",
            "native",
            "docs",
            "extension",
            "packaging",
        }:
            raise ValueError(f"invalid release area: {destination}")
        if not entry["reason"].strip():
            raise ValueError(f"missing reason: {destination}")
        source_hash = entry["source_sha256"]
        if not isinstance(source_hash, str) or not re_full_hash(source_hash):
            raise ValueError(f"invalid source hash: {source}")
        destination_hash = entry["destination_sha256"]
        if entry["classification"] == "deleted":
            if destination_hash is not None:
                raise ValueError(f"deleted destination hash must be null: {destination}")
        elif destination_hash != source_hash:
            raise ValueError(f"copied source and destination hashes differ: {destination}")
    return manifest


def re_full_hash(value: str) -> bool:
    return len(value) == 64 and value == value.upper() and all(
        character in "0123456789ABCDEF" for character in value
    )


def apply_manifest(
    manifest_path: Path,
    source_root: Path,
    destination_root: Path,
    summary_dir: Path,
) -> None:
    manifest = _load_manifest(manifest_path)
    source_root = source_root.resolve(strict=True)
    destination_root = destination_root.resolve(strict=True)
    current = str(_git(destination_root, "rev-parse", "HEAD")).strip()
    if current != manifest["destination_base_commit"]:
        raise ValueError(
            f"destination HEAD {current} is not manifest base "
            f"{manifest['destination_base_commit']}"
        )
    status = str(
        _git(
            destination_root,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        )
    )
    unexpected_status = [
        line
        for line in status.splitlines()
        if line[3:].replace("\\", "/") not in BOOTSTRAP_PATHS
    ]
    if unexpected_status:
        raise ValueError(
            f"destination has unreviewed pre-import changes: {unexpected_status}"
        )
    applied = []
    for entry in manifest["entries"]:
        source_path = entry["source_relative_path"]
        destination_path = entry["destination_relative_path"]
        destination = _resolve_confined(
            destination_root, destination_path, require_exists=False
        )
        classification = entry["classification"]
        if classification == "deleted":
            if not destination.is_file():
                raise ValueError(f"deletion target is missing: {destination_path}")
            base_content = _base_file(destination_root, current, destination_path)
            if (
                base_content is None
                or _sha256_bytes(base_content) != entry["source_sha256"]
            ):
                raise ValueError(f"deletion base hash mismatch: {destination_path}")
            clean = subprocess.run(
                ["git", "diff", "--quiet", "--", destination_path],
                cwd=destination_root,
                shell=False,
                check=False,
            )
            if clean.returncode != 0:
                raise ValueError(f"deletion target has local changes: {destination_path}")
            destination.unlink()
        else:
            source = _resolve_confined(source_root, source_path, require_exists=True)
            if not source.is_file():
                raise ValueError(f"source is missing: {source_path}")
            if _sha256_file(source) != entry["source_sha256"]:
                raise ValueError(f"source hash mismatch: {source_path}")
            if classification == "new" and destination.exists():
                raise ValueError(f"new destination already exists: {destination_path}")
            if classification == "modified" and not destination.is_file():
                raise ValueError(f"modified destination is missing: {destination_path}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
            source_mode = source.stat().st_mode
            if source_mode & stat.S_IXUSR:
                destination.chmod(destination.stat().st_mode | stat.S_IXUSR)
            if _sha256_file(destination) != entry["destination_sha256"]:
                raise ValueError(f"destination hash mismatch: {destination_path}")
        applied.append(entry)
    verify_manifest(manifest_path, destination_root, verify_diff=False)
    _write_summary(summary_dir, "apply", manifest, applied, [])


def verify_manifest(
    manifest_path: Path,
    destination_root: Path,
    *,
    verify_diff: bool,
) -> None:
    manifest = _load_manifest(manifest_path)
    destination_root = destination_root.resolve(strict=True)
    expected_paths = set()
    for entry in manifest["entries"]:
        destination_path = entry["destination_relative_path"]
        expected_paths.add(destination_path)
        destination = _resolve_confined(
            destination_root,
            destination_path,
            require_exists=entry["classification"] != "deleted",
        )
        if entry["classification"] == "deleted":
            if destination.exists():
                raise ValueError(f"deleted destination still exists: {destination_path}")
        elif _sha256_file(destination) != entry["destination_sha256"]:
            raise ValueError(f"destination hash drift: {destination_path}")
    if verify_diff:
        status = str(
            _git(
                destination_root,
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
            )
        ).strip()
        if status:
            raise ValueError(f"destination repository is dirty: {status}")
        base = manifest["destination_base_commit"]
        raw = _git(
            destination_root,
            "diff",
            "--name-only",
            "--no-renames",
            f"{base}..HEAD",
            "-z",
            text=False,
        )
        assert isinstance(raw, bytes)
        changed = {
            path.replace("\\", "/")
            for path in raw.decode("utf-8", "surrogateescape").split("\0")
            if path
        }
        unrecorded = changed - expected_paths - BOOTSTRAP_PATHS
        missing = expected_paths - changed
        if unrecorded:
            raise ValueError(f"unrecorded branch paths: {sorted(unrecorded)}")
        if missing:
            raise ValueError(f"manifest paths absent from branch diff: {sorted(missing)}")


def _write_summary(
    summary_dir: Path,
    operation: str,
    manifest: dict[str, Any],
    entries: list[dict[str, Any]],
    excluded: list[str],
) -> None:
    summary_dir = summary_dir.resolve()
    summary_dir.mkdir(parents=True, exist_ok=True)
    counts = {
        classification: sum(
            entry["classification"] == classification for entry in entries
        )
        for classification in ("new", "modified", "deleted")
    }
    summary = {
        "schema_id": "sona.source-import-summary.schema-1",
        "schema": 1,
        "sona_version": "0.15.3",
        "release_version": "0.15.3",
        "operation": operation,
        "source_commit": manifest["source_workspace_baseline"],
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
        "host_os": platform.system(),
        "architecture": platform.machine(),
        "tool_versions": {
            "python": platform.python_version(),
            "git": str(_git(Path.cwd(), "--version")).strip(),
        },
        "command_summary": [
            ["python", "tools/release/import_0153_manifest.py", operation]
        ],
        "destination_base_commit": manifest["destination_base_commit"],
        "counts": counts,
        "result_counters": {**counts, "fail": 0},
        "artifact_relative_evidence_paths": [
            f"sona-0.15.3-import-{operation}.json",
            f"sona-0.15.3-import-{operation}.md",
        ],
        "excluded": sorted(excluded),
        "entries": entries,
    }
    json_path = summary_dir / f"sona-0.15.3-import-{operation}.json"
    markdown_path = summary_dir / f"sona-0.15.3-import-{operation}.md"
    json_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    lines = [
        f"# Sona 0.15.3 Import {operation.title()} Summary",
        "",
        f"- Base commit: `{manifest['destination_base_commit']}`",
        f"- New: {counts['new']}",
        f"- Modified: {counts['modified']}",
        f"- Deleted: {counts['deleted']}",
        f"- Excluded observed paths: {len(excluded)}",
    ]
    markdown_path.write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
    )
    rendered = markdown_path.read_text(encoding="utf-8")
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    validated_lines = [
        f"# Sona 0.15.3 Import {loaded['operation'].title()} Summary",
        "",
        f"- Base commit: `{loaded['destination_base_commit']}`",
        f"- New: {loaded['counts']['new']}",
        f"- Modified: {loaded['counts']['modified']}",
        f"- Deleted: {loaded['counts']['deleted']}",
        f"- Excluded observed paths: {len(loaded['excluded'])}",
    ]
    if "\n".join(validated_lines) + "\n" != rendered:
        raise RuntimeError("import-summary Markdown does not match its JSON source")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create")
    create.add_argument("--source-root", type=Path, required=True)
    create.add_argument("--destination-base", required=True)
    create.add_argument("--output", type=Path, required=True)
    create.add_argument("--summary-dir", type=Path, required=True)

    apply = subparsers.add_parser("apply")
    apply.add_argument("--manifest", type=Path, required=True)
    apply.add_argument("--source-root", type=Path, required=True)
    apply.add_argument("--destination-root", type=Path, required=True)
    apply.add_argument("--summary-dir", type=Path, required=True)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--manifest", type=Path, required=True)
    verify.add_argument("--destination-root", type=Path, required=True)
    verify.add_argument("--verify-diff", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "create":
        if not _outside_root(args.summary_dir, args.source_root):
            parser.error("--summary-dir must resolve outside the source repository")
        create_manifest(
            args.source_root,
            args.destination_base,
            args.output,
            args.summary_dir,
        )
    elif args.command == "apply":
        if not _outside_root(args.summary_dir, args.destination_root):
            parser.error("--summary-dir must resolve outside the destination repository")
        apply_manifest(
            args.manifest,
            args.source_root,
            args.destination_root,
            args.summary_dir,
        )
    else:
        verify_manifest(
            args.manifest,
            args.destination_root,
            verify_diff=args.verify_diff,
        )
    return 0


def _outside_root(path: Path, root: Path) -> bool:
    resolved = path.resolve()
    root = root.resolve()
    return resolved != root and root not in resolved.parents


if __name__ == "__main__":
    raise SystemExit(main())
