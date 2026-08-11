#!/usr/bin/env python3
"""Certify one clean active Sona release commit outside its clone."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import time
import tomllib
import venv
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from email.parser import BytesParser
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

try:
    from .artifacts_0153 import inspect_archive
except ImportError:  # Direct script execution.
    from artifacts_0153 import inspect_archive


SCHEMA_ID = "sona.release-certification-platform.schema-1"
ROOT = Path(__file__).resolve().parents[2]
VERSION = str(
    tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
)
PHASES = {"python", "gates", "native", "extension", "packaging"}
TREE_EXCLUSIONS = {".git"}


@dataclass(frozen=True)
class CommandEvidence:
    argv: list[str]
    cwd: str
    exit_code: int
    duration_seconds: float
    timed_out: bool
    stdout_log: str
    stderr_log: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _inside(child: Path, parent: Path) -> bool:
    resolved_child = child.resolve()
    resolved_parent = parent.resolve()
    return resolved_child == resolved_parent or resolved_parent in resolved_child.parents


def require_external_root(repository: Path, cert_root: Path) -> Path:
    if not cert_root.is_absolute():
        raise ValueError("SONA_CERT_ROOT must be an absolute path")
    resolved = cert_root.resolve()
    if _inside(resolved, repository):
        raise ValueError("SONA_CERT_ROOT must resolve outside the repository")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )
    return completed.stdout.strip()


def clean_repository(repository: Path) -> None:
    status = git(repository, "status", "--porcelain=v1", "--untracked-files=all")
    if status:
        raise RuntimeError(f"certified repository is dirty:\n{status}")


def clone_tree_snapshot(repository: Path) -> dict[str, dict[str, Any]]:
    """Hash content and metadata for every non-.git clone-tree entry."""
    snapshot: dict[str, dict[str, Any]] = {}
    for path in sorted(repository.rglob("*")):
        relative = path.relative_to(repository)
        if relative.parts and relative.parts[0] in TREE_EXCLUSIONS:
            continue
        metadata = path.lstat()
        key = relative.as_posix()
        if path.is_symlink():
            kind = "symlink"
            digest = hashlib.sha256(os.readlink(path).encode("utf-8")).hexdigest()
            size = metadata.st_size
        elif path.is_file():
            kind = "file"
            digest = _sha256(path)
            size = metadata.st_size
        elif path.is_dir():
            kind = "directory"
            digest = None
            size = 0
        else:
            kind = "special"
            digest = None
            size = metadata.st_size
        snapshot[key] = {
            "kind": kind,
            "mode": metadata.st_mode,
            "size": size,
            "mtime_ns": metadata.st_mtime_ns,
            "sha256": digest,
        }
    return snapshot


def assert_clone_unchanged(
    repository: Path,
    baseline: dict[str, dict[str, Any]],
    phase: str,
) -> None:
    clean_repository(repository)
    current = clone_tree_snapshot(repository)
    if current != baseline:
        added = sorted(current.keys() - baseline.keys())
        removed = sorted(baseline.keys() - current.keys())
        changed = sorted(
            path
            for path in current.keys() & baseline.keys()
            if current[path] != baseline[path]
        )
        raise RuntimeError(
            f"clone tree changed during {phase}: "
            f"added={added[:10]} removed={removed[:10]} changed={changed[:10]}"
        )


def external_environment(cert_root: Path, source_commit: str) -> dict[str, str]:
    environment = dict(os.environ)
    paths = {
        "CARGO_TARGET_DIR": cert_root / "cargo-target",
        "TMPDIR": cert_root / "tmp",
        "TEMP": cert_root / "tmp",
        "TMP": cert_root / "tmp",
        "PYTHONPYCACHEPREFIX": cert_root / "pycache",
        "PIP_CACHE_DIR": cert_root / "pip-cache",
        "npm_config_cache": cert_root / "npm-cache",
        "XDG_CACHE_HOME": cert_root / "xdg-cache",
        "HYPOTHESIS_STORAGE_DIRECTORY": cert_root / "hypothesis",
        "COVERAGE_FILE": cert_root / "coverage" / ".coverage",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    environment.update({name: str(path) for name, path in paths.items()})
    environment["SONA_CERT_ROOT"] = str(cert_root)
    environment["SONA_SOURCE_COMMIT"] = source_commit
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["npm_config_update_notifier"] = "false"
    environment["NO_COLOR"] = "1"
    environment["FORCE_COLOR"] = "0"
    return environment


def _safe_argument(value: str, repository: Path, cert_root: Path) -> str:
    rendered = value.replace(str(repository), "<repository>")
    rendered = rendered.replace(str(cert_root), "<cert-root>")
    return rendered


class CommandRunner:
    def __init__(
        self,
        repository: Path,
        cert_root: Path,
        environment: dict[str, str],
    ) -> None:
        self.repository = repository
        self.cert_root = cert_root
        self.environment = environment
        self.evidence_dir = cert_root / "evidence" / "commands"
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.records: list[CommandEvidence] = []
        self._counter = 0

    def run(
        self,
        argv: Iterable[str | Path],
        *,
        cwd: Path,
        timeout: int = 1800,
        allowed_exit_codes: set[int] | None = None,
        environment: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [str(item) for item in argv]
        allowed = {0} if allowed_exit_codes is None else allowed_exit_codes
        self._counter += 1
        stem = f"{self._counter:03d}-{Path(command[0]).name}"
        stdout_path = self.evidence_dir / f"{stem}.stdout.txt"
        stderr_path = self.evidence_dir / f"{stem}.stderr.txt"
        process_environment = dict(self.environment)
        if environment:
            process_environment.update(environment)
        kwargs: dict[str, Any] = {
            "cwd": cwd,
            "env": process_environment,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
            "shell": False,
        }
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True
        started = time.monotonic()
        process = subprocess.Popen(command, **kwargs)
        timed_out = False
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name == "nt":
                subprocess.run(
                    ["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
                    capture_output=True,
                    shell=False,
                    check=False,
                )
            else:
                os.killpg(process.pid, signal.SIGTERM)
            try:
                stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                if os.name != "nt":
                    os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()
        duration = time.monotonic() - started
        stdout = stdout.replace("\r\n", "\n").replace("\r", "\n")
        stderr = stderr.replace("\r\n", "\n").replace("\r", "\n")
        stdout_path.write_text(stdout, encoding="utf-8", newline="\n")
        stderr_path.write_text(stderr, encoding="utf-8", newline="\n")
        record = CommandEvidence(
            argv=[
                _safe_argument(value, self.repository, self.cert_root)
                for value in command
            ],
            cwd=_safe_argument(str(cwd), self.repository, self.cert_root),
            exit_code=process.returncode if process.returncode is not None else 124,
            duration_seconds=round(duration, 3),
            timed_out=timed_out,
            stdout_log=stdout_path.relative_to(self.cert_root).as_posix(),
            stderr_log=stderr_path.relative_to(self.cert_root).as_posix(),
        )
        self.records.append(record)
        completed = subprocess.CompletedProcess(
            command,
            record.exit_code,
            stdout,
            stderr,
        )
        if timed_out:
            raise RuntimeError(f"command timed out after {timeout}s: {command}")
        if completed.returncode not in allowed:
            raise RuntimeError(
                f"command failed with exit {completed.returncode}: {command}\n"
                f"{stderr[-4000:]}"
            )
        return completed


def _extract_commit(repository: Path, commit: str, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    archive_path = destination.parent / f"{destination.name}.tar"
    subprocess.run(
        ["git", "archive", "--format=tar", "--output", str(archive_path), commit],
        cwd=repository,
        check=True,
        shell=False,
    )
    with tarfile.open(archive_path, "r:") as archive:
        for member in archive.getmembers():
            pure = PurePosixPath(member.name)
            if (
                pure.is_absolute()
                or any(part in {"", ".", ".."} for part in pure.parts)
                or member.issym()
                or member.islnk()
                or not (member.isfile() or member.isdir())
            ):
                raise RuntimeError(f"unsafe Git archive member: {member.name}")
            target = destination.joinpath(*pure.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise RuntimeError(f"Git archive file has no payload: {member.name}")
            with source, target.open("wb") as stream:
                shutil.copyfileobj(source, stream)
            target.chmod(member.mode & 0o777)


def _venv_python(path: Path) -> Path:
    return path / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _new_venv(path: Path) -> Path:
    venv.EnvBuilder(with_pip=True, clear=False).create(path)
    return _venv_python(path)


def _python_metadata(archive: Path) -> dict[str, Any]:
    if archive.suffix == ".whl":
        with zipfile.ZipFile(archive) as wheel:
            metadata_name = next(
                name for name in wheel.namelist() if name.endswith(".dist-info/METADATA")
            )
            raw = wheel.read(metadata_name)
    else:
        with tarfile.open(archive, "r:gz") as source:
            member = next(
                item for item in source.getmembers() if item.name.endswith("PKG-INFO")
            )
            stream = source.extractfile(member)
            if stream is None:
                raise RuntimeError(f"{archive.name} has no readable PKG-INFO")
            raw = stream.read()
    message = BytesParser().parsebytes(raw)
    requires_python = message["Requires-Python"]
    python_bounds = {
        bound.strip()
        for bound in (requires_python or "").split(",")
        if bound.strip()
    }
    if python_bounds != {">=3.11", "<3.13"}:
        raise RuntimeError(f"incorrect Requires-Python: {requires_python!r}")
    dependencies = message.get_all("Requires-Dist", [])
    forbidden_base = [
        item
        for item in dependencies
        if re.match(r"(?i)^(torch|transformers|accelerate|openai|anthropic)\b", item)
        and "extra ==" not in item
    ]
    if forbidden_base:
        raise RuntimeError(f"heavy dependency leaked into base metadata: {forbidden_base}")
    return {
        "requires_python": requires_python,
        "requires_dist": dependencies,
    }


def _copy_tree(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination)


def _tree_bytes(root: Path, suffix: str = ".js") -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob(f"*{suffix}"))
        if path.is_file()
    }


def node_command(name: str) -> str:
    if name not in {"npm", "npx"}:
        raise ValueError(f"unsupported Node command shim: {name}")
    return f"{name}.cmd" if os.name == "nt" else name


def npm_ci_command() -> list[str]:
    return [
        node_command("npm"),
        "ci",
        "--omit=optional",
        "--no-audit",
        "--fund=false",
    ]


def run_python_phase(
    stage: Path,
    cert_root: Path,
    runner: CommandRunner,
) -> dict[str, Any]:
    phase_root = cert_root / "python"
    phase_root.mkdir(parents=True, exist_ok=True)
    python = _new_venv(phase_root / "venv")
    runner.run(
        [python, "-m", "pip", "install", "--upgrade", "pip", "build"],
        cwd=stage,
    )
    runner.run([python, "-m", "pip", "install", "-e", ".[dev]"], cwd=stage)
    pytest_args = [
        python,
        "-m",
        "pytest",
        "tests",
        "-q",
        "-o",
        f"cache_dir={phase_root / 'pytest-cache'}",
        "--basetemp",
        phase_root / "pytest-temp",
    ]
    pytest_result = runner.run(pytest_args, cwd=stage, timeout=3600)
    warning_pattern = re.compile(
        r"(?m)^.*[\\/]lark[\\/]utils\.py:(?P<line>163|164): "
        r"(?P<category>DeprecationWarning): (?P<message>module "
        r"'sre_(?:parse|constants)' is deprecated)$"
    )
    warnings = [
        {
            "category": match.group("category"),
            "origin": f"lark/utils.py:{match.group('line')}",
            "message": match.group("message"),
            "count": 1,
        }
        for match in warning_pattern.finditer(pytest_result.stdout)
    ]
    summary_match = re.search(r"(?m)(\d+) warnings? in ", pytest_result.stdout)
    reported_warning_count = int(summary_match.group(1)) if summary_match else 0
    if reported_warning_count != len(warnings):
        raise RuntimeError(
            "pytest emitted an unreviewed warning: "
            f"reported={reported_warning_count} reviewed={len(warnings)}"
        )
    pytest_counts = {
        label.replace(" ", "_"): int(count)
        for count, label in re.findall(
            r"(\d+) (passed|failed|skipped|errors?|warnings?)",
            pytest_result.stdout,
        )
    }
    if pytest_counts.get("skipped", 0) != 0:
        raise RuntimeError(f"the mandatory Python suite skipped tests: {pytest_counts}")
    if (
        pytest_counts.get("failed", 0) != 0
        or pytest_counts.get("error", 0) != 0
        or pytest_counts.get("errors", 0) != 0
    ):
        raise RuntimeError(f"the mandatory Python suite did not pass: {pytest_counts}")
    runner.run([python, "tools/run_examples.py"], cwd=stage)
    for probe in ("stdlib", "accessibility", "guardian"):
        runner.run([python, "-m", "sona", "probe", probe], cwd=stage)
    runner.run(
        [python, "tools/validate_release_metadata.py", "--version", VERSION],
        cwd=stage,
    )
    hello = phase_root / "hello.sona"
    hello.write_text('print("Hello, Sona!")\n', encoding="utf-8", newline="\n")
    performance = {
        "version": ([python, "-m", "sona", "--version"], 1.0),
        "help": ([python, "-m", "sona", "--help"], 1.0),
        "check": ([python, "-m", "sona", "check", hello], 2.0),
        "run": ([python, "-m", "sona", str(hello)], 3.0),
    }
    medians: dict[str, float] = {}
    for name, (command, limit) in performance.items():
        samples = []
        for _ in range(3):
            started = time.monotonic()
            runner.run(command, cwd=stage, timeout=30)
            samples.append(time.monotonic() - started)
        median = sorted(samples)[1]
        if median > limit:
            raise RuntimeError(
                f"{name} median {median:.3f}s exceeds {limit:.3f}s"
            )
        medians[name] = round(median, 3)
    return {
        "status": "pass",
        "python": runner.run(
            [python, "--version"], cwd=stage
        ).stdout.strip(),
        "performance_medians_seconds": medians,
        "pytest_counts": pytest_counts,
        "accepted_warnings": warnings,
    }


def run_gates_phase(
    stage: Path,
    cert_root: Path,
    runner: CommandRunner,
    python: Path,
    native_binary: Path | None,
) -> dict[str, Any]:
    gate_root = cert_root / "reports" / "gates"
    runner.run(
        [
            python,
            "tests/release/run_0153_release_gate.py",
            "--output-dir",
            gate_root / "release",
        ],
        cwd=stage,
        timeout=180,
    )
    result: dict[str, Any] = {
        "status": "pass",
        "release_gate": f"reports/gates/release/sona-{VERSION}-release-gate.json",
    }
    if native_binary is not None:
        runner.run(
            [
                python,
                "tests/conformance/run_0153_differential_conformance.py",
                "--native-binary",
                native_binary,
                "--output-dir",
                gate_root / "differential",
                "--sona-version",
                VERSION,
            ],
            cwd=stage,
            timeout=300,
        )
        runner.run(
            [
                python,
                "tests/release/run_0153_native_standalone_gate.py",
                "--native-binary",
                native_binary,
                "--output-dir",
                gate_root / "native-standalone",
                "--sona-version",
                VERSION,
            ],
            cwd=stage,
            timeout=300,
        )
        result.update(
            {
                "differential":
                    "reports/gates/differential/"
                    f"sona-{VERSION}-differential-conformance.json",
                "native_standalone":
                    "reports/gates/native-standalone/"
                    f"sona-{VERSION}-native-standalone.json",
            }
        )
    return result


def _rust_sources(stage: Path) -> list[Path]:
    return sorted((stage / "native").rglob("*.rs"))


def _linux_python_free_proof(
    stage: Path,
    cert_root: Path,
    runner: CommandRunner,
    binary: Path,
) -> dict[str, Any]:
    file_result = runner.run(["file", str(binary)], cwd=stage)
    if "statically linked" not in file_result.stdout.lower():
        raise RuntimeError("musl binary is not reported as statically linked")
    ldd_result = runner.run(
        ["ldd", str(binary)],
        cwd=stage,
        allowed_exit_codes={0, 1},
    )
    dependency_text = (ldd_result.stdout + ldd_result.stderr).lower()
    if "python" in dependency_text:
        raise RuntimeError("musl binary dependency inspection references Python")
    if not (
        "not a dynamic executable" in dependency_text
        or "statically linked" in dependency_text
    ):
        raise RuntimeError(f"unexpected ldd result: {dependency_text.strip()}")
    context = cert_root / "native" / "scratch-context"
    context.mkdir(parents=True, exist_ok=True)
    shutil.copy2(binary, context / "sona")
    shutil.copy2(stage / "native/tests/conformance/hello.sona", context / "hello.sona")
    shutil.copy2(
        stage / "tests/release/native-scratch.Dockerfile",
        context / "Dockerfile",
    )
    expected_dockerfile = (
        "FROM scratch\n"
        "COPY sona /sona\n"
        "COPY hello.sona /hello.sona\n"
        'ENTRYPOINT ["/sona", "run", "/hello.sona", "--engine", "native"]\n'
    )
    if (context / "Dockerfile").read_text(encoding="utf-8") != expected_dockerfile:
        raise RuntimeError("scratch proof Dockerfile differs from the reviewed contract")
    if {path.name for path in context.iterdir()} != {
        "Dockerfile",
        "hello.sona",
        "sona",
    }:
        raise RuntimeError("scratch proof context contains unexpected material")
    image = f"sona-native-cert-{os.getpid()}"
    runner.run(["docker", "build", "--no-cache", "-t", image, str(context)], cwd=stage)
    inspection = runner.run(
        [
            "docker",
            "image",
            "inspect",
            image,
            "--format",
            "{{json .Config.Entrypoint}}",
        ],
        cwd=stage,
    )
    if json.loads(inspection.stdout) != [
        "/sona",
        "run",
        "/hello.sona",
        "--engine",
        "native",
    ]:
        raise RuntimeError("scratch image does not directly execute the native binary")
    completed = runner.run(["docker", "run", "--rm", image], cwd=stage, timeout=60)
    if completed.stdout != "Hello from native Sona\n" or completed.stderr:
        raise RuntimeError("scratch-container output did not match exactly")
    runner.run(["docker", "image", "rm", "--force", image], cwd=stage)
    return {
        "status": "pass",
        "file": file_result.stdout.strip(),
        "ldd": dependency_text.strip(),
        "container_output": completed.stdout,
    }


def _windows_pe_inspection(
    stage: Path,
    runner: CommandRunner,
    binary: Path,
) -> dict[str, Any]:
    dumpbin = shutil.which("dumpbin")
    llvm_readobj = shutil.which("llvm-readobj")
    if dumpbin:
        completed = runner.run([dumpbin, "/DEPENDENTS", str(binary)], cwd=stage)
        tool = "dumpbin"
    elif llvm_readobj:
        completed = runner.run([llvm_readobj, "--coff-imports", str(binary)], cwd=stage)
        tool = "llvm-readobj"
    else:
        raise RuntimeError("required PE import inspection tooling is unavailable")
    imports = completed.stdout + completed.stderr
    if re.search(r"(?i)python(?:3\d+)?\.dll", imports):
        raise RuntimeError("Windows native binary imports a Python DLL")
    return {"status": "pass", "tool": tool, "python_dll_imported": False}


def run_native_phase(
    stage: Path,
    cert_root: Path,
    runner: CommandRunner,
) -> tuple[dict[str, Any], Path]:
    manifest = stage / "native/Cargo.toml"
    rustc_version = runner.run(["rustc", "--version"], cwd=stage).stdout.strip()
    if not rustc_version.startswith("rustc 1.94.0 "):
        raise RuntimeError(f"Rust 1.94.0 is required: {rustc_version}")
    runner.run(["cargo", "metadata", "--locked", "--manifest-path", manifest], cwd=stage)
    runner.run(
        ["rustfmt", "--edition", "2021", "--check", *_rust_sources(stage)],
        cwd=stage,
    )
    runner.run(
        [
            "cargo",
            "clippy",
            "--manifest-path",
            manifest,
            "--workspace",
            "--all-targets",
            "--all-features",
            "--locked",
            "--",
            "-D",
            "warnings",
        ],
        cwd=stage,
        timeout=3600,
    )
    runner.run(
        [
            "cargo",
            "test",
            "--manifest-path",
            manifest,
            "--workspace",
            "--all-targets",
            "--all-features",
            "--locked",
        ],
        cwd=stage,
        timeout=3600,
    )
    runner.run(
        ["cargo", "build", "--manifest-path", manifest, "--release", "--locked"],
        cwd=stage,
        timeout=3600,
    )
    binary_name = "sona.exe" if os.name == "nt" else "sona"
    target_dir = Path(runner.environment["CARGO_TARGET_DIR"])
    binary = target_dir / "release" / binary_name
    if not binary.is_file():
        raise RuntimeError(f"native release binary is missing: {binary}")
    proof: dict[str, Any] = {"status": "not_applicable"}
    certified_binary = binary
    if platform.system() == "Linux":
        runner.run(
            [
                "cargo",
                "build",
                "--manifest-path",
                manifest,
                "--release",
                "--locked",
                "--target",
                "x86_64-unknown-linux-musl",
            ],
            cwd=stage,
            timeout=3600,
        )
        certified_binary = (
            target_dir / "x86_64-unknown-linux-musl" / "release" / "sona"
        )
        proof = _linux_python_free_proof(stage, cert_root, runner, certified_binary)
    elif platform.system() == "Windows":
        proof = _windows_pe_inspection(stage, runner, certified_binary)
    raw_name = (
        f"sona-native-{VERSION}-windows-x86_64.exe"
        if platform.system() == "Windows"
        else f"sona-native-{VERSION}-linux-x86_64-musl"
        if platform.system() == "Linux"
        else f"sona-native-{VERSION}-macos-{platform.machine()}"
    )
    raw_binary = cert_root / "artifacts" / "raw" / raw_name
    raw_binary.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(certified_binary, raw_binary)
    return (
        {
            "status": "pass",
            "cargo": runner.run(["cargo", "--version"], cwd=stage).stdout.strip(),
            "rustc": rustc_version,
            "python_free_proof": proof,
            "binary": raw_binary.relative_to(cert_root).as_posix(),
            "binary_sha256": _sha256(raw_binary),
        },
        certified_binary,
    )


def run_extension_phase(
    stage: Path,
    cert_root: Path,
    runner: CommandRunner,
) -> dict[str, Any]:
    extension = cert_root / "extension" / "source"
    _copy_tree(stage / "vscode-extension", extension)
    expected_out = _tree_bytes(extension / "out")
    extension_commands = []
    extension_commands.append(runner.run(
        npm_ci_command(),
        cwd=extension,
        timeout=1800,
    ))
    extension_commands.append(
        runner.run([node_command("npm"), "run", "compile"], cwd=extension)
    )
    actual_out = _tree_bytes(extension / "out")
    if actual_out != expected_out:
        changed = sorted(set(actual_out) ^ set(expected_out))
        changed.extend(
            path
            for path in set(actual_out) & set(expected_out)
            if actual_out[path] != expected_out[path]
        )
        raise RuntimeError(f"compiled extension output drift: {sorted(set(changed))}")
    extension_commands.append(
        runner.run([node_command("npm"), "test"], cwd=extension)
    )
    audit = runner.run(
        [
            node_command("npm"),
            "audit",
            "--omit=dev",
            "--audit-level=high",
            "--json",
        ],
        cwd=extension,
    )
    audit_path = cert_root / "evidence" / "npm-audit-production.json"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(audit.stdout, encoding="utf-8", newline="\n")
    payload = json.loads(audit.stdout)
    vulnerabilities = payload.get("metadata", {}).get("vulnerabilities", {})
    if vulnerabilities.get("high") != 0 or vulnerabilities.get("critical") != 0:
        raise RuntimeError(f"production npm audit failed: {vulnerabilities}")
    complete_audit = runner.run(
        [node_command("npm"), "audit", "--audit-level=high", "--json"],
        cwd=extension,
    )
    complete_audit_path = cert_root / "evidence" / "npm-audit-complete.json"
    complete_audit_path.write_text(
        complete_audit.stdout, encoding="utf-8", newline="\n"
    )
    complete_payload = json.loads(complete_audit.stdout)
    complete_vulnerabilities = complete_payload.get("metadata", {}).get(
        "vulnerabilities", {}
    )
    if any(
        complete_vulnerabilities.get(level) != 0
        for level in ("info", "low", "moderate", "high", "critical")
    ):
        raise RuntimeError(
            f"complete npm audit has a security advisory: "
            f"{complete_vulnerabilities}"
        )
    vsix = cert_root / "artifacts" / f"sona-ai-native-programming-{VERSION}.vsix"
    vsix.parent.mkdir(parents=True, exist_ok=True)
    extension_commands.append(runner.run(
        [
            node_command("npx"),
            "--no-install",
            "vsce",
            "package",
            "--out",
            vsix,
        ],
        cwd=extension,
        timeout=600,
    ))
    warning_pattern = re.compile(r"(?mi)^\s*(?:npm WARN|WARNING\b|warning:)")
    for completed in extension_commands:
        if warning_pattern.search(completed.stdout + completed.stderr):
            raise RuntimeError(
                f"extension command emitted an unaccepted warning: {completed.args}"
            )
    inspection = inspect_archive(vsix, kind="vsix")
    node_version = runner.run(["node", "--version"], cwd=extension).stdout.strip()
    if node_version != "v20.19.5":
        raise RuntimeError(f"the pinned Node v20.19.5 is required: {node_version}")
    return {
        "status": "pass",
        "node": node_version,
        "npm": runner.run(
            [node_command("npm"), "--version"], cwd=extension
        ).stdout.strip(),
        "audit": vulnerabilities,
        "complete_audit": complete_vulnerabilities,
        "vsix": vsix.relative_to(cert_root).as_posix(),
        "inspection": inspection,
    }


def run_packaging_phase(
    stage: Path,
    cert_root: Path,
    runner: CommandRunner,
) -> dict[str, Any]:
    packaging_source = cert_root / "packaging" / "source"
    _copy_tree(stage, packaging_source)
    venv_python = _new_venv(cert_root / "packaging" / "build-venv")
    runner.run(
        [venv_python, "-m", "pip", "install", "--upgrade", "pip", "build"],
        cwd=packaging_source,
    )
    output = cert_root / "artifacts"
    output.mkdir(parents=True, exist_ok=True)
    runner.run(
        [venv_python, "-m", "build", "--outdir", output],
        cwd=packaging_source,
        timeout=900,
    )
    wheel = output / f"sona_lang-{VERSION}-py3-none-any.whl"
    source = output / f"sona_lang-{VERSION}.tar.gz"
    if not wheel.is_file() or not source.is_file():
        raise RuntimeError("Python build did not produce the required filenames")
    metadata = {
        wheel.name: _python_metadata(wheel),
        source.name: _python_metadata(source),
    }
    inspections = {
        wheel.name: inspect_archive(wheel, kind="python"),
        source.name: inspect_archive(source, kind="python"),
    }
    install_python = _new_venv(cert_root / "packaging" / "install-venv")
    runner.run([install_python, "-m", "pip", "install", wheel], cwd=cert_root)
    runner.run([install_python, "-m", "sona", "--version"], cwd=cert_root)
    isolation = runner.run(
        [
            install_python,
            "-c",
            (
                "import json,sys,sona;"
                "heavy={'torch','transformers','accelerate','openai','anthropic'};"
                "print(json.dumps(sorted(heavy & set(sys.modules))))"
            ),
        ],
        cwd=cert_root,
    )
    if isolation.stdout != "[]\n":
        raise RuntimeError(f"base install loaded heavy modules: {isolation.stdout!r}")
    return {
        "status": "pass",
        "artifacts": [wheel.name, source.name],
        "metadata": metadata,
        "inspections": inspections,
        "heavy_import_isolation": "pass",
    }


def _tool_version(
    runner: CommandRunner,
    command: list[str],
    cwd: Path,
) -> str:
    try:
        completed = runner.run(command, cwd=cwd, timeout=60)
    except (FileNotFoundError, RuntimeError):
        return "unavailable"
    return (completed.stdout or completed.stderr).strip().splitlines()[0]


def _write_platform_report(
    cert_root: Path,
    commit: str,
    phases: dict[str, Any],
    runner: CommandRunner,
) -> Path:
    report = {
        "schema_id": SCHEMA_ID,
        "schema": 1,
        "sona_version": VERSION,
        "source_commit": commit,
        "generated_at_utc": _utc_now(),
        "host_os": platform.system(),
        "architecture": platform.machine(),
        "tool_versions": {
            "python": platform.python_version(),
            "git": _tool_version(runner, ["git", "--version"], ROOT),
        },
        "command_summary": [record.argv for record in runner.records],
        "result_counters": {
            "pass": sum(value.get("status") == "pass" for value in phases.values()),
            "fail": 0,
        },
        "artifact_relative_evidence_paths": sorted(
            path.relative_to(cert_root).as_posix()
            for evidence_root in (
                cert_root / "evidence",
                cert_root / "reports" / "gates",
                cert_root / "artifacts",
            )
            if evidence_root.exists()
            for path in evidence_root.rglob("*")
            if path.is_file()
        ),
        "phases": phases,
        "commands": [asdict(record) for record in runner.records],
    }
    reports = cert_root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    path = reports / (
        f"sona-{VERSION}-{platform.system().lower()}-"
        f"python-{sys.version_info.major}.{sys.version_info.minor}-certification.json"
    )
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


def run_certification(
    repository: Path,
    cert_root: Path,
    requested_phases: set[str],
) -> Path:
    repository = repository.resolve(strict=True)
    cert_root = require_external_root(repository, cert_root)
    clean_repository(repository)
    commit = git(repository, "rev-parse", "HEAD")
    baseline = clone_tree_snapshot(repository)
    environment = external_environment(cert_root, commit)
    runner = CommandRunner(repository, cert_root, environment)

    results: dict[str, Any] = {}
    python = Path(sys.executable)
    native_binary: Path | None = None
    order = ["python", "native", "gates", "extension", "packaging"]
    for phase in order:
        if phase not in requested_phases:
            continue
        stage = cert_root / "stages" / phase
        stage.parent.mkdir(parents=True, exist_ok=True)
        _extract_commit(repository, commit, stage)
        assert_clone_unchanged(repository, baseline, f"{phase} source staging")
        if phase == "python":
            results[phase] = run_python_phase(stage, cert_root, runner)
            python = _venv_python(cert_root / "python" / "venv")
        elif phase == "native":
            results[phase], native_binary = run_native_phase(stage, cert_root, runner)
        elif phase == "gates":
            if "python" not in requested_phases:
                harness = cert_root / "gates" / "venv"
                python = _new_venv(harness)
                runner.run(
                    [python, "-m", "pip", "install", "--upgrade", "pip"],
                    cwd=stage,
                )
                runner.run([python, "-m", "pip", "install", stage], cwd=stage)
            results[phase] = run_gates_phase(
                stage, cert_root, runner, python, native_binary
            )
        elif phase == "extension":
            results[phase] = run_extension_phase(stage, cert_root, runner)
        elif phase == "packaging":
            results[phase] = run_packaging_phase(stage, cert_root, runner)
        assert_clone_unchanged(repository, baseline, phase)
    report = _write_platform_report(cert_root, commit, results, runner)
    assert_clone_unchanged(repository, baseline, "report generation")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=ROOT)
    parser.add_argument(
        "--cert-root",
        type=Path,
        default=Path(os.environ["SONA_CERT_ROOT"])
        if os.environ.get("SONA_CERT_ROOT")
        else None,
    )
    parser.add_argument(
        "--phases",
        default=",".join(sorted(PHASES)),
        help="Comma-separated subset of python,gates,native,extension,packaging",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Validate the clean clone and external root without running phases.",
    )
    args = parser.parse_args(argv)
    if args.cert_root is None:
        parser.error("--cert-root or SONA_CERT_ROOT is required")
    requested = {item.strip() for item in args.phases.split(",") if item.strip()}
    unknown = requested - PHASES
    if unknown:
        parser.error(f"unknown phases: {sorted(unknown)}")
    repository = args.repository.resolve(strict=True)
    cert_root = require_external_root(repository, args.cert_root)
    clean_repository(repository)
    if args.preflight_only:
        print(f"preflight pass: repository={repository} cert_root={cert_root}")
        return 0
    report = run_certification(repository, cert_root, requested)
    print(f"Sona {VERSION} platform certification passed: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
