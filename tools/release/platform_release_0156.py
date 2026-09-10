#!/usr/bin/env python3
"""Build, inspect, verify, and assemble Sona 0.15.6 platform artifacts.

The script intentionally uses only the Python standard library. Native release
archives are accepted only when they are built and executed on the matching
host operating system and architecture. Cross-compilation alone is not a
release-support claim.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import importlib.metadata
import io
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from email import policy
from email.parser import BytesParser
from pathlib import Path, PurePosixPath
from typing import Any

VERSION = "0.15.6"
ROOT = Path(__file__).resolve().parents[2]
NATIVE_REPORT_SCHEMA = "sona.native-platform-build.schema-1"
PORTABLE_REPORT_SCHEMA = "sona.portable-platform-build.schema-1"
VERIFY_REPORT_SCHEMA = "sona.platform-verification.schema-1"
RELEASE_MANIFEST_SCHEMA = "sona.cross-platform-release.schema-1"


@dataclass(frozen=True)
class NativeSpec:
    platform: str
    architecture: str
    rust_target: str
    archive_name: str
    archive_member: str
    report_name: str


def _spec(platform_id: str, architecture: str, target: str, suffix: str) -> NativeSpec:
    stem = f"sona-native-{VERSION}-{platform_id}-{suffix}"
    extension = ".zip" if platform_id == "windows" else ".tar.gz"
    return NativeSpec(
        platform=platform_id,
        architecture=architecture,
        rust_target=target,
        archive_name=f"{stem}{extension}",
        archive_member="sona.exe" if platform_id == "windows" else "sona",
        report_name=f"{stem}-report.json",
    )


NATIVE_SPECS = {
    ("windows", "x86_64"): _spec("windows", "x86_64", "x86_64-pc-windows-msvc", "x86_64"),
    ("linux", "x86_64"): _spec("linux", "x86_64", "x86_64-unknown-linux-musl", "x86_64-musl"),
    ("linux", "aarch64"): _spec("linux", "aarch64", "aarch64-unknown-linux-musl", "aarch64-musl"),
    ("macos", "x86_64"): _spec("macos", "x86_64", "x86_64-apple-darwin", "x86_64"),
    ("macos", "aarch64"): _spec("macos", "aarch64", "aarch64-apple-darwin", "aarch64"),
}

WHEEL_NAME = f"sona_lang-{VERSION}-py3-none-any.whl"
SDIST_NAME = f"sona_lang-{VERSION}.tar.gz"
VSIX_NAME = f"sona-ai-native-programming-{VERSION}.vsix"
TEST_KIT_NAME = f"sona-{VERSION}-platform-test-kit.zip"
PORTABLE_REPORT_NAME = f"sona-{VERSION}-portable-report.json"
RELEASE_MANIFEST_NAME = f"sona-{VERSION}-release-manifest.json"
PORTABLE_ASSETS = {WHEEL_NAME, SDIST_NAME, VSIX_NAME, TEST_KIT_NAME}
NATIVE_ASSETS = {item.archive_name for item in NATIVE_SPECS.values()}
RELEASE_ASSETS = PORTABLE_ASSETS | NATIVE_ASSETS


def _utc_now() -> str:
    return dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest().lower()


def _normalize_architecture(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_")
    if normalized in {"x86_64", "amd64", "x64"}:
        return "x86_64"
    if normalized in {"aarch64", "arm64", "arm64v8"}:
        return "aarch64"
    return normalized


def _host_platform() -> str:
    if hasattr(sys, "getandroidapilevel") or os.environ.get("ANDROID_ROOT"):
        return "android"
    system = platform.system().lower()
    return {"windows": "windows", "linux": "linux", "darwin": "macos"}.get(system, system)


def _host_architecture() -> str:
    return _normalize_architecture(platform.machine())


def _repository_version() -> str:
    pyproject = ROOT / "pyproject.toml"
    if not pyproject.is_file():
        return VERSION
    payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return str(payload["project"]["version"])


def _require_release_version() -> None:
    actual = _repository_version()
    if actual != VERSION:
        raise RuntimeError(f"repository version is {actual}, expected {VERSION}")


def _git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        shell=False,
    )
    return completed.stdout.strip()


def _source_commit() -> str:
    configured = os.environ.get("GITHUB_SHA")
    candidate = configured.strip() if configured else _git("rev-parse", "HEAD")
    normalized = candidate.lower()
    if not re.fullmatch(r"[0-9a-f]{40}", normalized):
        raise RuntimeError("source commit must be a complete 40-character Git SHA")
    return normalized


def _source_revision_for_build() -> str | None:
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        return _source_commit()
    try:
        dirty = _git("status", "--porcelain", "--untracked-files=normal")
    except (OSError, subprocess.CalledProcessError):
        return None
    if dirty:
        return None
    return _source_commit()


def _source_epoch(explicit: int | None = None) -> int:
    if explicit is not None:
        return explicit
    configured = os.environ.get("SOURCE_DATE_EPOCH")
    if configured:
        return int(configured)
    return int(_git("show", "-s", "--format=%ct", "HEAD"))


def _run(
    arguments: Sequence[str | Path],
    *,
    cwd: Path,
    environment: dict[str, str] | None = None,
    timeout: int = 600,
    allowed_exit_codes: Iterable[int] = (0,),
) -> subprocess.CompletedProcess[str]:
    command = [str(item) for item in arguments]
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        shell=False,
        timeout=timeout,
    )
    allowed = set(allowed_exit_codes)
    if completed.returncode not in allowed:
        output = (completed.stdout + completed.stderr)[-6000:]
        raise RuntimeError(
            f"command failed with exit {completed.returncode}: {command!r}\n{output}"
        )
    return completed


def _safe_member(name: str) -> PurePosixPath:
    if "\\" in name:
        raise RuntimeError(f"archive member uses a backslash: {name}")
    pure = PurePosixPath(name)
    if pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        raise RuntimeError(f"unsafe archive member: {name}")
    return pure


def _zip_datetime(epoch: int) -> tuple[int, int, int, int, int, int]:
    minimum = 315532800  # ZIP timestamps begin in 1980.
    value = dt.datetime.fromtimestamp(max(epoch, minimum), dt.UTC)
    return (
        value.year,
        value.month,
        value.day,
        value.hour,
        value.minute,
        value.second // 2 * 2,
    )


def _write_zip(
    destination: Path,
    entries: Sequence[tuple[str, bytes, int]],
    *,
    epoch: int,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w") as archive:
        for name, content, mode in sorted(entries, key=lambda item: item[0]):
            _safe_member(name)
            info = zipfile.ZipInfo(name, _zip_datetime(epoch))
            info.create_system = 3
            info.external_attr = mode << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content)


def _write_tar_gz(
    destination: Path,
    entries: Sequence[tuple[str, bytes, int]],
    *,
    epoch: int,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with (
        destination.open("wb") as raw,
        gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=epoch) as stream,
        tarfile.open(fileobj=stream, mode="w", format=tarfile.PAX_FORMAT) as archive,
    ):
        for name, content, mode in sorted(entries, key=lambda item: item[0]):
            _safe_member(name)
            info = tarfile.TarInfo(name)
            info.size = len(content)
            info.mtime = epoch
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.mode = mode
            archive.addfile(info, io.BytesIO(content))


def _spec_for_archive(path: Path) -> NativeSpec:
    matches = [item for item in NATIVE_SPECS.values() if item.archive_name == path.name]
    if len(matches) != 1:
        raise RuntimeError(f"unsupported native archive name: {path.name}")
    return matches[0]


def _build_native_archive(binary: Path, spec: NativeSpec, output: Path, epoch: int) -> None:
    content = binary.read_bytes()
    entries = [(spec.archive_member, content, 0o755)]
    if spec.platform == "windows":
        _write_zip(output, entries, epoch=epoch)
    else:
        _write_tar_gz(output, entries, epoch=epoch)


def inspect_native_archive(path: Path, expected: NativeSpec | None = None) -> dict[str, Any]:
    path = path.resolve(strict=True)
    spec = expected or _spec_for_archive(path)
    if path.name != spec.archive_name:
        raise RuntimeError(f"archive name {path.name} does not match {spec.archive_name}")
    if spec.platform == "windows":
        if not zipfile.is_zipfile(path):
            raise RuntimeError("Windows Native Core artifact must be a ZIP")
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) != 1 or members[0].filename != spec.archive_member:
                raise RuntimeError("native archive must contain exactly its Sona executable")
            info = members[0]
            _safe_member(info.filename)
            if info.is_dir() or (info.external_attr >> 16 & 0o777) != 0o755:
                raise RuntimeError("native ZIP executable mode is not normalized")
            binary_hash = _sha256_bytes(archive.read(info))
    else:
        if zipfile.is_zipfile(path):
            raise RuntimeError("Unix Native Core artifact must be a tar.gz archive")
        with tarfile.open(path, "r:gz") as archive:
            members = archive.getmembers()
            if len(members) != 1 or members[0].name != spec.archive_member:
                raise RuntimeError("native archive must contain exactly its Sona executable")
            info = members[0]
            _safe_member(info.name)
            if not info.isfile() or info.issym() or info.islnk():
                raise RuntimeError("native archive member must be a regular file")
            if info.mode != 0o755 or info.uid != 0 or info.gid != 0:
                raise RuntimeError("native tar metadata is not normalized")
            stream = archive.extractfile(info)
            if stream is None:
                raise RuntimeError("native tar executable has no payload")
            binary_hash = _sha256_bytes(stream.read())
    return {
        "status": "pass",
        "filename": path.name,
        "platform": spec.platform,
        "architecture": spec.architecture,
        "rust_target": spec.rust_target,
        "members": 1,
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
        "binary_sha256": binary_hash,
    }


def _extract_native_archive(path: Path, destination: Path) -> tuple[NativeSpec, Path]:
    spec = _spec_for_archive(path)
    inspect_native_archive(path, spec)
    destination.mkdir(parents=True, exist_ok=False)
    binary = destination / spec.archive_member
    if spec.platform == "windows":
        with zipfile.ZipFile(path) as archive:
            content = archive.read(spec.archive_member)
    else:
        with tarfile.open(path, "r:gz") as archive:
            stream = archive.extractfile(spec.archive_member)
            if stream is None:
                raise RuntimeError("native executable has no payload")
            content = stream.read()
    binary.write_bytes(content)
    binary.chmod(0o755)
    return spec, binary


def _archive_names(path: Path) -> list[str]:
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            names = [item.filename for item in archive.infolist()]
    else:
        with tarfile.open(path, "r:gz") as archive:
            names = [item.name for item in archive.getmembers()]
    for name in names:
        _safe_member(name)
    if len(names) != len(set(names)):
        raise RuntimeError(f"archive contains duplicate members: {path.name}")
    return names


def _metadata_from_wheel(path: Path) -> Any:
    with zipfile.ZipFile(path) as archive:
        metadata_names = [
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        ]
        if len(metadata_names) != 1:
            raise RuntimeError("wheel must contain exactly one METADATA file")
        return BytesParser(policy=policy.default).parsebytes(archive.read(metadata_names[0]))


def _metadata_from_sdist(path: Path) -> Any:
    with tarfile.open(path, "r:gz") as archive:
        matches = [
            item
            for item in archive.getmembers()
            if PurePosixPath(item.name).name == "PKG-INFO"
            and len(PurePosixPath(item.name).parts) == 2
        ]
        if len(matches) != 1:
            raise RuntimeError("sdist must contain exactly one top-level PKG-INFO file")
        member = matches[0]
        if not member.isfile() or member.issym() or member.islnk():
            raise RuntimeError("sdist PKG-INFO must be a regular file")
        stream = archive.extractfile(member)
        if stream is None:
            raise RuntimeError("sdist PKG-INFO has no payload")
        return BytesParser(policy=policy.default).parsebytes(stream.read())


def _validate_python_metadata(message: Any) -> None:
    if str(message["Name"]).lower().replace("_", "-") != "sona-lang":
        raise RuntimeError(f"unexpected package name: {message['Name']!r}")
    if message["Version"] != VERSION:
        raise RuntimeError(f"unexpected package version: {message['Version']!r}")
    bounds = {part.strip() for part in str(message["Requires-Python"]).split(",") if part.strip()}
    if bounds != {">=3.11", "<3.13"}:
        raise RuntimeError(f"unexpected Python bounds: {message['Requires-Python']!r}")


def inspect_wheel(path: Path) -> dict[str, Any]:
    path = path.resolve(strict=True)
    if path.name != WHEEL_NAME or not zipfile.is_zipfile(path):
        raise RuntimeError(f"expected wheel named {WHEEL_NAME}")
    names = _archive_names(path)
    forbidden = [
        name
        for name in names
        if name.endswith((".pyc", ".map"))
        or "/__pycache__/" in name
        or name.startswith(("tests/", "docs/", "native/"))
    ]
    if forbidden:
        raise RuntimeError(f"wheel contains forbidden members: {forbidden[:5]}")
    if not any(name == "sona/stdlib/MANIFEST.json" for name in names):
        raise RuntimeError("wheel is missing the standard-library manifest")
    _validate_python_metadata(_metadata_from_wheel(path))
    return {
        "status": "pass",
        "filename": path.name,
        "kind": "wheel",
        "members": len(names),
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def inspect_sdist(path: Path) -> dict[str, Any]:
    path = path.resolve(strict=True)
    if path.name != SDIST_NAME or zipfile.is_zipfile(path):
        raise RuntimeError(f"expected source distribution named {SDIST_NAME}")
    names = _archive_names(path)
    with tarfile.open(path, "r:gz") as archive:
        for member in archive.getmembers():
            if member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                raise RuntimeError(f"sdist contains unsafe member type: {member.name}")
    forbidden = [
        name
        for name in names
        if name.endswith((".pyc", ".map", ".vsix", ".zip"))
        or "/__pycache__/" in name
        or "/node_modules/" in name
        or "/target/" in name
    ]
    if forbidden:
        raise RuntimeError(f"sdist contains forbidden members: {forbidden[:5]}")
    _validate_python_metadata(_metadata_from_sdist(path))
    return {
        "status": "pass",
        "filename": path.name,
        "kind": "sdist",
        "members": len(names),
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def inspect_vsix(path: Path) -> dict[str, Any]:
    path = path.resolve(strict=True)
    if path.name != VSIX_NAME or not zipfile.is_zipfile(path):
        raise RuntimeError(f"expected VSIX named {VSIX_NAME}")
    names = _archive_names(path)
    forbidden = [
        name
        for name in names
        if name.lower().endswith((".map", ".ts"))
        or name.lower().startswith("extension/src/")
        or "/node_modules/" in name.lower()
        or "/native/target/" in name.lower()
    ]
    if forbidden:
        raise RuntimeError(f"VSIX contains forbidden members: {forbidden[:5]}")
    with zipfile.ZipFile(path) as archive:
        required = {
            "extension/package.json",
            "extension/out/extension.js",
            "extension/assets/icon.png",
        }
        missing = required - set(names)
        if missing:
            raise RuntimeError(f"VSIX is missing required members: {sorted(missing)}")
        package = json.loads(archive.read("extension/package.json"))
    if package.get("version") != VERSION:
        raise RuntimeError(f"VSIX version is {package.get('version')!r}, expected {VERSION}")
    if package.get("main") != "./out/extension.js":
        raise RuntimeError("VSIX entry point is not the reviewed bundle")
    return {
        "status": "pass",
        "filename": path.name,
        "kind": "vsix",
        "members": len(names),
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _build_test_kit(destination: Path, epoch: int) -> dict[str, Any]:
    guide = ROOT / "docs/guides/platform-installation-and-testing.md"
    if not guide.is_file():
        raise RuntimeError(f"platform guide is missing: {guide}")
    prefix = f"sona-{VERSION}-platform-test-kit"
    entries = [
        (f"{prefix}/README.md", guide.read_bytes(), 0o644),
        (f"{prefix}/verify.py", Path(__file__).read_bytes(), 0o755),
        (
            f"{prefix}/hello.sona",
            b'print("Sona 0.15.6 platform test kit: OK")\n',
            0o644,
        ),
    ]
    _write_zip(destination, entries, epoch=epoch)
    with zipfile.ZipFile(destination) as archive:
        names = archive.namelist()
        if names != sorted(names) or len(names) != 3:
            raise RuntimeError("test kit ZIP is not deterministic")
    return {
        "status": "pass",
        "filename": destination.name,
        "kind": "test-kit",
        "members": 3,
        "bytes": destination.stat().st_size,
        "sha256": _sha256(destination),
    }


def _native_smoke(binary: Path) -> dict[str, Any]:
    expected = "Sona 0.15.6 cross-platform Native Core: OK"
    with tempfile.TemporaryDirectory(prefix="sona-0156-native-smoke-") as raw:
        root = Path(raw)
        source = root / "hello.sona"
        source.write_text(f'print("{expected}")\n', encoding="ascii", newline="\n")
        receipts = root / "receipts"
        receipts.mkdir()
        receipt = receipts / "native-proof.json"
        version = _run([binary, "--version"], cwd=root, timeout=30)
        if VERSION not in version.stdout:
            raise RuntimeError(f"native version output is unexpected: {version.stdout!r}")
        _run([binary, "check", source], cwd=root, timeout=30)
        normal = _run([binary, "run", source, "--engine", "native"], cwd=root, timeout=30)
        if normal.stdout.strip() != expected:
            raise RuntimeError(f"native run output is unexpected: {normal.stdout!r}")
        proof = _run(
            [
                binary,
                "proof",
                source,
                "--receipt",
                receipt,
                "--engine",
                "native",
            ],
            cwd=root,
            timeout=30,
        )
        if proof.stdout.strip() != expected or not receipt.is_file():
            raise RuntimeError("Native Proof did not preserve output and publish a receipt")
        payload = json.loads(receipt.read_text(encoding="utf-8"))
        if payload.get("schema_id") != "sona.native-proof.schema-1":
            raise RuntimeError("Native Proof receipt has the wrong schema")
        if payload.get("sona_version") != VERSION:
            raise RuntimeError("Native Proof receipt has the wrong Sona version")
        if payload.get("execution", {}).get("status") != "ok":
            raise RuntimeError("Native Proof receipt did not record success")
        engine = payload.get("engine", {})
        if (
            engine.get("name") != "native"
            or engine.get("python_required") is not False
            or engine.get("python_embedded") is not False
            or engine.get("fallback_used") is not False
        ):
            raise RuntimeError(f"Native Proof engine claim is invalid: {engine}")
        return {
            "status": "pass",
            "version": version.stdout.strip(),
            "stdout_sha256": _sha256_bytes(normal.stdout.encode("utf-8")),
            "proof_schema": payload["schema_id"],
            "receipt_hash": payload.get("receipt_hash"),
        }


def _dependency_inspection(binary: Path, spec: NativeSpec) -> dict[str, Any]:
    if spec.platform == "linux":
        file_tool = shutil.which("file")
        ldd_tool = shutil.which("ldd")
        if not file_tool or not ldd_tool:
            raise RuntimeError("Linux release inspection requires file and ldd")
        file_result = _run([file_tool, binary], cwd=binary.parent)
        if "static" not in file_result.stdout.lower():
            raise RuntimeError(f"Linux musl binary is not static: {file_result.stdout}")
        ldd = _run([ldd_tool, binary], cwd=binary.parent, allowed_exit_codes=(0, 1))
        dependencies = (ldd.stdout + ldd.stderr).lower()
        if "python" in dependencies:
            raise RuntimeError("Linux Native Core binary references Python")
        if not ("not a dynamic executable" in dependencies or "statically linked" in dependencies):
            raise RuntimeError(f"unexpected ldd result: {dependencies.strip()}")
        return {
            "status": "pass",
            "tool": "file+ldd",
            "file": file_result.stdout.strip(),
            "python_dependency": False,
        }
    if spec.platform == "macos":
        file_tool = shutil.which("file")
        otool = shutil.which("otool")
        if not file_tool or not otool:
            raise RuntimeError("macOS release inspection requires file and otool")
        file_result = _run([file_tool, binary], cwd=binary.parent)
        if spec.architecture not in file_result.stdout.lower().replace("arm64", "aarch64"):
            raise RuntimeError(f"macOS binary architecture is unexpected: {file_result.stdout}")
        linked = _run([otool, "-L", binary], cwd=binary.parent)
        if "python" in (linked.stdout + linked.stderr).lower():
            raise RuntimeError("macOS Native Core binary references Python")
        return {
            "status": "pass",
            "tool": "file+otool",
            "file": file_result.stdout.strip(),
            "python_dependency": False,
        }
    candidates = [
        ("dumpbin", ["/DEPENDENTS", str(binary)]),
        ("llvm-readobj", ["--coff-imports", str(binary)]),
        ("objdump", ["-p", str(binary)]),
    ]
    for name, arguments in candidates:
        tool = shutil.which(name)
        if not tool:
            continue
        inspected = _run([tool, *arguments], cwd=binary.parent)
        dependencies = inspected.stdout + inspected.stderr
        if re.search(r"(?i)python(?:3\d+)?\.dll", dependencies):
            raise RuntimeError("Windows Native Core binary imports a Python DLL")
        return {"status": "pass", "tool": name, "python_dependency": False}
    raise RuntimeError("Windows release inspection requires dumpbin, llvm-readobj, or objdump")


def _rustc_host_target(verbose_output: str) -> str:
    for line in verbose_output.splitlines():
        if line.startswith("host: "):
            host = line.removeprefix("host: ").strip()
            if host:
                return host
    raise RuntimeError("rustc -vV did not report a host target")


def _cargo_target_arguments(spec: NativeSpec, rustc_host: str) -> list[str]:
    if rustc_host == spec.rust_target:
        return []
    return ["--target", spec.rust_target]


def _cargo_build(spec: NativeSpec, output_dir: Path) -> tuple[Path, dict[str, Any]]:
    manifest = ROOT / "native/Cargo.toml"
    target_dir = Path(
        os.environ.get(
            "CARGO_TARGET_DIR",
            str(output_dir.parent / f"cargo-target-{spec.rust_target}"),
        )
    ).resolve()
    environment = os.environ.copy()
    environment["CARGO_TARGET_DIR"] = str(target_dir)
    source_revision = _source_revision_for_build()
    if source_revision is None:
        environment.pop("SONA_SOURCE_COMMIT", None)
    else:
        environment["SONA_SOURCE_COMMIT"] = source_revision
    rustc = _run(["rustc", "--version"], cwd=ROOT, environment=environment)
    if not rustc.stdout.startswith("rustc 1.94.0 "):
        raise RuntimeError(f"Rust 1.94.0 is required: {rustc.stdout.strip()}")
    rustc_verbose = _run(["rustc", "-vV"], cwd=ROOT, environment=environment)
    rustc_host = _rustc_host_target(rustc_verbose.stdout)
    target_arguments = _cargo_target_arguments(spec, rustc_host)
    _run(
        ["cargo", "fmt", "--manifest-path", manifest, "--all", "--", "--check"],
        cwd=ROOT,
        environment=environment,
    )
    _run(
        [
            "cargo",
            "clippy",
            "--manifest-path",
            manifest,
            "--workspace",
            "--all-targets",
            "--all-features",
            "--locked",
            *target_arguments,
            "--",
            "-D",
            "warnings",
        ],
        cwd=ROOT,
        environment=environment,
        timeout=3600,
    )
    _run(
        [
            "cargo",
            "test",
            "--manifest-path",
            manifest,
            "--workspace",
            "--all-targets",
            "--all-features",
            "--locked",
            *target_arguments,
        ],
        cwd=ROOT,
        environment=environment,
        timeout=3600,
    )
    _run(
        [
            "cargo",
            "build",
            "--manifest-path",
            manifest,
            "--release",
            "--locked",
            *target_arguments,
        ],
        cwd=ROOT,
        environment=environment,
        timeout=3600,
    )
    target_output = target_dir if not target_arguments else target_dir / spec.rust_target
    binary = target_output / "release" / spec.archive_member
    if not binary.is_file():
        raise RuntimeError(f"cargo did not produce the required binary: {binary}")
    return binary, {
        "mode": "source",
        "rustc": rustc.stdout.strip(),
        "cargo": _run(["cargo", "--version"], cwd=ROOT, environment=environment).stdout.strip(),
        "rustc_host": rustc_host,
        "source_revision_embedded": source_revision is not None,
        "target_mode": "host-default" if not target_arguments else "explicit",
        "target_dir": str(target_dir),
    }


def command_native(args: argparse.Namespace) -> dict[str, Any]:
    _require_release_version()
    key = (args.platform, _normalize_architecture(args.architecture))
    if key not in NATIVE_SPECS:
        raise RuntimeError(f"unsupported native platform: {key}")
    spec = NATIVE_SPECS[key]
    if args.target != spec.rust_target:
        raise RuntimeError(f"target must be {spec.rust_target} for {key}")
    host = (_host_platform(), _host_architecture())
    if host != key:
        raise RuntimeError(
            f"release native builds must run on their matching host: host={host}, requested={key}"
        )
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.binary:
        binary = args.binary.resolve(strict=True)
        build = {"mode": "prebuilt", "rustc": "not-recorded", "cargo": "not-recorded"}
    else:
        binary, build = _cargo_build(spec, output_dir)
    smoke = _native_smoke(binary)
    if args.development_skip_dependency_inspection:
        dependency = {"status": "development-skip", "python_dependency": "unknown"}
    else:
        dependency = _dependency_inspection(binary, spec)
    archive = output_dir / spec.archive_name
    _build_native_archive(binary, spec, archive, _source_epoch(args.epoch))
    inspection = inspect_native_archive(archive, spec)
    report = {
        "schema_id": NATIVE_REPORT_SCHEMA,
        "schema": 1,
        "sona_version": VERSION,
        "source_commit": _source_commit(),
        "generated_at_utc": _utc_now(),
        "host": {"platform": host[0], "architecture": host[1]},
        "target": asdict(spec),
        "build": build,
        "dependency_inspection": dependency,
        "smoke": smoke,
        "artifact": inspection,
        "status": "pass",
    }
    report_path = output_dir / spec.report_name
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return {"status": "pass", "archive": str(archive), "report": str(report_path)}


def command_portable(args: argparse.Namespace) -> dict[str, Any]:
    _require_release_version()
    wheel = args.wheel.resolve(strict=True)
    sdist = args.sdist.resolve(strict=True)
    vsix = args.vsix.resolve(strict=True)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    inspections = {
        WHEEL_NAME: inspect_wheel(wheel),
        SDIST_NAME: inspect_sdist(sdist),
        VSIX_NAME: inspect_vsix(vsix),
    }
    for source in (wheel, sdist, vsix):
        shutil.copy2(source, output_dir / source.name)
    kit = output_dir / TEST_KIT_NAME
    inspections[TEST_KIT_NAME] = _build_test_kit(kit, _source_epoch(args.epoch))
    report = {
        "schema_id": PORTABLE_REPORT_SCHEMA,
        "schema": 1,
        "sona_version": VERSION,
        "source_commit": _source_commit(),
        "generated_at_utc": _utc_now(),
        "artifacts": inspections,
        "status": "pass",
    }
    report_path = output_dir / PORTABLE_REPORT_NAME
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return {"status": "pass", "artifacts": sorted(inspections), "report": str(report_path)}


def _json_command(
    command: Sequence[str | Path], cwd: Path, *, expected_status: str
) -> dict[str, Any]:
    completed = _run(command, cwd=cwd, timeout=120)
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"command did not return JSON: {command!r}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"command did not return a JSON object: {command!r}")
    if payload.get("status") != expected_status:
        raise RuntimeError(
            f"command returned status {payload.get('status')!r}, "
            f"expected {expected_status!r}: {command!r}"
        )
    return payload


def _python_guardian_smoke(
    sona_prefix: Sequence[str | Path], native_binary: Path | None
) -> dict[str, Any]:
    expected = "Sona 0.15.6 platform Python and Guardian: OK"
    with tempfile.TemporaryDirectory(prefix="sona-0156-platform-verify-") as raw:
        root = Path(raw)
        source = root / "hello.sona"
        source.write_text(f'print("{expected}")\n', encoding="ascii", newline="\n")
        receipts = root / ".sona" / "receipts"
        receipts.mkdir(parents=True)
        version = _run([*sona_prefix, "--version"], cwd=root, timeout=30)
        if VERSION not in version.stdout:
            raise RuntimeError(f"Python CLI version output is unexpected: {version.stdout!r}")
        _run([*sona_prefix, "check", source], cwd=root, timeout=30)
        executed = _run([*sona_prefix, "run", source], cwd=root, timeout=30)
        if executed.stdout.strip() != expected:
            raise RuntimeError(f"Python CLI run output is unexpected: {executed.stdout!r}")
        _json_command(
            [*sona_prefix, "guardian", "init", "--project-root", root],
            root,
            expected_status="initialized",
        )
        _json_command(
            [*sona_prefix, "guardian", "verify", "--project-root", root],
            root,
            expected_status="ok",
        )
        result: dict[str, Any] = {
            "status": "pass",
            "version": version.stdout.strip(),
            "python_run": "pass",
            "guardian_baseline": "ok",
            "guardian_bound_proof": "not-tested",
        }
        if native_binary is None:
            return result
        receipt = receipts / "guardian-bound-proof.json"
        proof = _run(
            [
                native_binary,
                "proof",
                source,
                "--receipt",
                receipt,
                "--engine",
                "native",
                "--guardian-root",
                root,
            ],
            cwd=root,
            timeout=60,
        )
        if proof.stdout.strip() != expected or not receipt.is_file():
            raise RuntimeError("Guardian-bound Native Proof did not publish expected evidence")
        verified = _json_command(
            [
                *sona_prefix,
                "guardian",
                "proof",
                "verify",
                "--project-root",
                root,
                "--receipt",
                receipt,
            ],
            root,
            expected_status="verified",
        )
        _json_command(
            [
                *sona_prefix,
                "guardian",
                "proof",
                "attest",
                "--project-root",
                root,
                "--receipt",
                receipt,
            ],
            root,
            expected_status="attested",
        )
        review = _json_command(
            [
                *sona_prefix,
                "guardian",
                "proof",
                "review",
                "--project-root",
                root,
                "--receipt",
                receipt,
                "--provider",
                "deterministic",
            ],
            root,
            expected_status="reviewed",
        )
        history_completed = _run(
            [
                *sona_prefix,
                "guardian",
                "proof",
                "history",
                "--project-root",
                root,
                "--limit",
                "10",
            ],
            cwd=root,
            timeout=120,
        )
        try:
            history_payload = json.loads(history_completed.stdout)
        except json.JSONDecodeError as error:
            raise RuntimeError("Guardian Proof history did not return JSON") from error
        if isinstance(history_payload, list):
            history_records = history_payload
        elif isinstance(history_payload, dict):
            if history_payload.get("status") not in {None, "ok"}:
                raise RuntimeError(
                    "Guardian Proof history returned an unexpected status: "
                    f"{history_payload.get('status')!r}"
                )
            history_records = history_payload.get("records", [])
        else:
            raise RuntimeError("Guardian Proof history returned an unsupported JSON shape")
        if not history_records:
            raise RuntimeError("Guardian Proof history did not contain the attestation")
        result.update(
            {
                "guardian_bound_proof": "pass",
                "proof_receipt_hash": verified.get("receipt_hash"),
                "review_input_hash": review.get("review_input_hash"),
                "attestation_records": len(history_records),
            }
        )
        return result


def command_verify(args: argparse.Namespace) -> dict[str, Any]:
    wheel = args.wheel.resolve(strict=True)
    inspections: dict[str, Any] = {WHEEL_NAME: inspect_wheel(wheel)}
    if args.sdist:
        inspections[SDIST_NAME] = inspect_sdist(args.sdist.resolve(strict=True))
    if args.vsix:
        inspections[VSIX_NAME] = inspect_vsix(args.vsix.resolve(strict=True))
    if args.sona_executable:
        sona_prefix: list[str | Path] = [args.sona_executable.resolve(strict=True)]
        installed_distribution = "external-cli"
    else:
        try:
            installed = importlib.metadata.version("sona-lang")
        except importlib.metadata.PackageNotFoundError as error:
            raise RuntimeError(
                "sona-lang is not installed in this Python environment; "
                "install the supplied wheel first"
            ) from error
        if installed != VERSION:
            raise RuntimeError(f"installed sona-lang is {installed}, expected {VERSION}")
        sona_prefix = [sys.executable, "-m", "sona"]
        installed_distribution = installed
    native_inspection: dict[str, Any] | None = None
    native_smoke: dict[str, Any] | None = None
    with tempfile.TemporaryDirectory(prefix="sona-0156-native-extract-") as raw:
        native_binary: Path | None = None
        if args.native_archive:
            archive = args.native_archive.resolve(strict=True)
            native_inspection = inspect_native_archive(archive)
            spec, native_binary = _extract_native_archive(archive, Path(raw) / "native")
            host = (_host_platform(), _host_architecture())
            if host != (spec.platform, spec.architecture):
                raise RuntimeError(
                    "native archive does not match this host: "
                    f"archive={(spec.platform, spec.architecture)}, host={host}"
                )
            native_smoke = _native_smoke(native_binary)
        elif not args.python_only:
            raise RuntimeError("provide --native-archive or explicitly use --python-only")
        guardian = _python_guardian_smoke(sona_prefix, native_binary)
    report = {
        "schema_id": VERIFY_REPORT_SCHEMA,
        "schema": 1,
        "sona_version": VERSION,
        "generated_at_utc": _utc_now(),
        "host": {
            "platform": _host_platform(),
            "architecture": _host_architecture(),
            "python": platform.python_version(),
        },
        "installed_distribution": installed_distribution,
        "portable_artifacts": inspections,
        "native_artifact": native_inspection,
        "native_smoke": native_smoke,
        "python_guardian_smoke": guardian,
        "status": "pass",
    }
    if args.report:
        report_path = args.report.resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return report


def _find_unique(root: Path, name: str) -> Path:
    matches = [path for path in root.rglob(name) if path.is_file()]
    if len(matches) != 1:
        raise RuntimeError(f"expected one {name!r} under {root}, found {len(matches)}")
    return matches[0]


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON report is not an object: {path}")
    return payload


def command_assemble(args: argparse.Namespace) -> dict[str, Any]:
    _require_release_version()
    input_root = args.input_root.resolve(strict=True)
    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError("assembly output directory must be empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    portable_report = _load_json(_find_unique(input_root, PORTABLE_REPORT_NAME))
    if portable_report.get("schema_id") != PORTABLE_REPORT_SCHEMA:
        raise RuntimeError("portable report has the wrong schema")
    if portable_report.get("status") != "pass":
        raise RuntimeError("portable report did not pass")
    source_commit = portable_report.get("source_commit")
    reports: dict[str, Any] = {}
    for spec in NATIVE_SPECS.values():
        report = _load_json(_find_unique(input_root, spec.report_name))
        if report.get("schema_id") != NATIVE_REPORT_SCHEMA or report.get("status") != "pass":
            raise RuntimeError(f"native report did not pass: {spec.report_name}")
        if report.get("source_commit") != source_commit:
            raise RuntimeError("platform reports do not identify the same source commit")
        if report.get("host") != {
            "platform": spec.platform,
            "architecture": spec.architecture,
        }:
            raise RuntimeError(f"native report host mismatch: {spec.report_name}")
        if report.get("target") != asdict(spec):
            raise RuntimeError(f"native report target mismatch: {spec.report_name}")
        if report.get("build", {}).get("mode") != "source":
            raise RuntimeError(f"native artifact was not built from source: {spec.report_name}")
        if report.get("dependency_inspection", {}).get("status") != "pass":
            raise RuntimeError(f"native dependency inspection did not pass: {spec.report_name}")
        if report.get("smoke", {}).get("status") != "pass":
            raise RuntimeError(f"native smoke test did not pass: {spec.report_name}")
        archive = _find_unique(input_root, spec.archive_name)
        inspection = inspect_native_archive(archive, spec)
        if report.get("artifact", {}).get("sha256") != inspection["sha256"]:
            raise RuntimeError(f"native archive hash does not match report: {archive.name}")
        reports[spec.archive_name] = report
    github_sha = os.environ.get("GITHUB_SHA")
    if github_sha and github_sha != source_commit:
        raise RuntimeError("platform evidence does not match the current GitHub commit")
    inspections: dict[str, Any] = {}
    for name in sorted(RELEASE_ASSETS):
        source = _find_unique(input_root, name)
        destination = output_dir / name
        shutil.copy2(source, destination)
        if name == WHEEL_NAME:
            inspections[name] = inspect_wheel(destination)
        elif name == SDIST_NAME:
            inspections[name] = inspect_sdist(destination)
        elif name == VSIX_NAME:
            inspections[name] = inspect_vsix(destination)
        elif name == TEST_KIT_NAME:
            if not zipfile.is_zipfile(destination):
                raise RuntimeError("platform test kit is not a ZIP")
            inspections[name] = {
                "status": "pass",
                "filename": name,
                "sha256": _sha256(destination),
                "bytes": destination.stat().st_size,
            }
        else:
            inspections[name] = inspect_native_archive(destination)
        if name in PORTABLE_ASSETS:
            reported = portable_report.get("artifacts", {}).get(name, {})
            if reported.get("sha256") != inspections[name]["sha256"]:
                raise RuntimeError(f"portable artifact hash does not match its report: {name}")
    manifest = {
        "schema_id": RELEASE_MANIFEST_SCHEMA,
        "schema": 1,
        "sona_version": VERSION,
        "source_commit": source_commit,
        "generated_at_utc": _utc_now(),
        "desktop_support": [
            {
                "platform": spec.platform,
                "architecture": spec.architecture,
                "rust_target": spec.rust_target,
                "artifact": spec.archive_name,
                "host_built": True,
                "host_executed": True,
            }
            for spec in sorted(
                NATIVE_SPECS.values(), key=lambda item: (item.platform, item.architecture)
            )
        ],
        "portable_assets": sorted(PORTABLE_ASSETS),
        "artifacts": [inspections[name] for name in sorted(inspections)],
        "mobile": {
            "android": "experimental compile/Python-only evaluation; not a 0.15.6 release target",
            "ios": "compile-only evaluation; no standalone CLI release target",
        },
        "status": "pass",
    }
    manifest_path = output_dir / RELEASE_MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    checksum_paths = sorted([*output_dir.glob("*")], key=lambda path: path.name)
    checksum_lines = [f"{_sha256(path)}  {path.name}" for path in checksum_paths if path.is_file()]
    checksums = output_dir / "SHA256SUMS.txt"
    checksums.write_text("\n".join(checksum_lines) + "\n", encoding="ascii", newline="\n")
    return {
        "status": "pass",
        "source_commit": source_commit,
        "output_dir": str(output_dir),
        "artifacts": sorted(path.name for path in output_dir.iterdir() if path.is_file()),
    }


def command_inspect(args: argparse.Namespace) -> dict[str, Any]:
    path = args.artifact.resolve(strict=True)
    if path.name == WHEEL_NAME:
        return inspect_wheel(path)
    if path.name == SDIST_NAME:
        return inspect_sdist(path)
    if path.name == VSIX_NAME:
        return inspect_vsix(path)
    if path.name in NATIVE_ASSETS:
        return inspect_native_archive(path)
    raise RuntimeError(f"unsupported artifact name: {path.name}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    native = commands.add_parser("native", help="Build, test, and package one host-native target")
    native.add_argument("--platform", choices=["windows", "linux", "macos"], required=True)
    native.add_argument("--architecture", choices=["x86_64", "aarch64"], required=True)
    native.add_argument("--target", required=True)
    native.add_argument("--output-dir", type=Path, required=True)
    native.add_argument("--binary", type=Path, help="Development-only prebuilt binary input")
    native.add_argument("--epoch", type=int)
    native.add_argument(
        "--development-skip-dependency-inspection",
        action="store_true",
        help="Local development only; assembly rejects reports with this status",
    )

    portable = commands.add_parser(
        "portable", help="Inspect and collect wheel, sdist, VSIX, and test kit"
    )
    portable.add_argument("--wheel", type=Path, required=True)
    portable.add_argument("--sdist", type=Path, required=True)
    portable.add_argument("--vsix", type=Path, required=True)
    portable.add_argument("--output-dir", type=Path, required=True)
    portable.add_argument("--epoch", type=int)

    verify = commands.add_parser(
        "verify", help="Run machine-local artifact and trust-chain verification"
    )
    verify.add_argument("--wheel", type=Path, required=True)
    verify.add_argument("--sdist", type=Path)
    verify.add_argument("--vsix", type=Path)
    verify.add_argument("--native-archive", type=Path)
    verify.add_argument("--python-only", action="store_true")
    verify.add_argument("--sona-executable", type=Path)
    verify.add_argument("--report", type=Path)

    assemble = commands.add_parser(
        "assemble", help="Assemble the exact cross-platform release candidate"
    )
    assemble.add_argument("--input-root", type=Path, required=True)
    assemble.add_argument("--output-dir", type=Path, required=True)

    inspect = commands.add_parser("inspect", help="Inspect one release artifact")
    inspect.add_argument("--artifact", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {
        "native": command_native,
        "portable": command_portable,
        "verify": command_verify,
        "assemble": command_assemble,
        "inspect": command_inspect,
    }
    try:
        result = handlers[args.command](args)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

