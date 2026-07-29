#!/usr/bin/env python3
"""Assemble authoritative Sona 0.15.3 release assets from certified evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .artifacts_0153 import (
        build_native_archive,
        build_source_archive,
        inspect_archive,
        source_epoch,
    )
    from .certify_0153 import (
        assert_clone_unchanged,
        clean_repository,
        clone_tree_snapshot,
        require_external_root,
    )
except ImportError:  # Direct script execution.
    from artifacts_0153 import (
        build_native_archive,
        build_source_archive,
        inspect_archive,
        source_epoch,
    )
    from certify_0153 import (
        assert_clone_unchanged,
        clean_repository,
        clone_tree_snapshot,
        require_external_root,
    )


VERSION = "0.15.3"
SCHEMA_ID = "sona.release-certification.schema-1"
ROOT = Path(__file__).resolve().parents[2]
AUTHORITY_FILES = {
    "SHA256SUMS",
    f"sona-{VERSION}-certification.json",
    f"sona-{VERSION}-certification.md",
}
PUBLISHED_FILES = {
    f"sona_lang-{VERSION}-py3-none-any.whl",
    f"sona_lang-{VERSION}.tar.gz",
    f"sona-native-{VERSION}-windows-x86_64.zip",
    f"sona-native-{VERSION}-linux-x86_64-musl.tar.gz",
    f"sona-ai-native-programming-{VERSION}.vsix",
    f"sona-{VERSION}-source.tar.gz",
    "SHA256SUMS",
    f"sona-{VERSION}-certification.json",
    f"sona-{VERSION}-certification.md",
    f"RELEASE_NOTES_v{VERSION}.md",
    f"{VERSION}-implementation-report.md",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _git(repository: Path, *arguments: str, text: bool = True) -> str | bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=text,
        shell=False,
    )
    return completed.stdout


def _find_unique(root: Path, filename: str) -> Path:
    matches = [path for path in root.rglob(filename) if path.is_file()]
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one {filename!r} under {root}, found {len(matches)}"
        )
    return matches[0]


def _copy_unique(input_root: Path, output_root: Path, filename: str) -> Path:
    source = _find_unique(input_root, filename)
    destination = output_root / filename
    shutil.copy2(source, destination)
    return destination


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} does not contain a JSON object")
    return payload


def _validate_platform_evidence(
    input_root: Path,
    source_commit: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    paths = sorted(input_root.rglob("sona-0.15.3-*-certification.json"))
    reports = [_load_json(path) for path in paths]
    if not reports:
        raise RuntimeError("no platform certification reports were supplied")
    for path, report in zip(paths, reports):
        if report.get("schema_id") != "sona.release-certification-platform.schema-1":
            raise RuntimeError(f"wrong platform report schema: {path}")
        if report.get("sona_version") != VERSION:
            raise RuntimeError(f"wrong Sona version in {path}")
        if report.get("source_commit") != source_commit:
            raise RuntimeError(f"source commit mismatch in {path}")
        if report.get("result_counters", {}).get("fail") != 0:
            raise RuntimeError(f"failed platform certification report: {path}")
        if any(command.get("timed_out") for command in report.get("commands", [])):
            raise RuntimeError(f"timed-out command recorded in {path}")
        evidence_paths = report.get("artifact_relative_evidence_paths", [])
        if any("\\" in evidence for evidence in evidence_paths):
            raise RuntimeError(f"non-POSIX evidence path in {path}")
        python_phase = report.get("phases", {}).get("python")
        if python_phase:
            if python_phase.get("pytest_counts", {}).get("skipped", 0) != 0:
                raise RuntimeError(f"mandatory Python tests were skipped in {path}")
            allowed_warnings = {
                (
                    "DeprecationWarning",
                    "lark/utils.py:163",
                    "module 'sre_parse' is deprecated",
                    1,
                ),
                (
                    "DeprecationWarning",
                    "lark/utils.py:164",
                    "module 'sre_constants' is deprecated",
                    1,
                ),
            }
            observed_warnings = {
                (
                    warning.get("category"),
                    warning.get("origin"),
                    warning.get("message"),
                    warning.get("count"),
                )
                for warning in python_phase.get("accepted_warnings", [])
            }
            if not observed_warnings <= allowed_warnings:
                raise RuntimeError(f"unreviewed Python warning in {path}")

    expected_python = {
        (system, version)
        for system in ("Linux", "Windows", "Darwin")
        for version in ("3.11", "3.12")
    }
    observed_python = {
        (
            report["host_os"],
            ".".join(report["tool_versions"]["python"].split(".")[:2]),
        )
        for report in reports
        if report.get("phases", {}).get("python", {}).get("status") == "pass"
    }
    if observed_python != expected_python:
        raise RuntimeError(
            f"incomplete Python matrix: expected={sorted(expected_python)} "
            f"observed={sorted(observed_python)}"
        )
    native_systems = {
        report["host_os"]
        for report in reports
        if report.get("phases", {}).get("native", {}).get("status") == "pass"
        and report.get("phases", {}).get("gates", {}).get("status") == "pass"
    }
    if native_systems != {"Linux", "Windows", "Darwin"}:
        raise RuntimeError(f"incomplete Native Core matrix: {sorted(native_systems)}")
    linux = next(
        report for report in reports
        if report["host_os"] == "Linux" and "native" in report.get("phases", {})
    )
    windows = next(
        report for report in reports
        if report["host_os"] == "Windows" and "native" in report.get("phases", {})
    )
    if linux["phases"]["native"]["python_free_proof"].get("status") != "pass":
        raise RuntimeError("Linux Python-free proof did not pass")
    if windows["phases"]["native"]["python_free_proof"].get("status") != "pass":
        raise RuntimeError("Windows Python-free proof did not pass")
    extension = [
        report for report in reports
        if report.get("phases", {}).get("extension", {}).get("status") == "pass"
    ]
    if len(extension) != 1:
        raise RuntimeError("exactly one extension certification report is required")
    vulnerabilities = extension[0]["phases"]["extension"]["audit"]
    if vulnerabilities.get("high") != 0 or vulnerabilities.get("critical") != 0:
        raise RuntimeError("production extension audit is not clean")
    complete_vulnerabilities = extension[0]["phases"]["extension"][
        "complete_audit"
    ]
    if any(
        complete_vulnerabilities.get(level) != 0
        for level in ("info", "low", "moderate", "high", "critical")
    ):
        raise RuntimeError("complete extension audit is not clean")
    if extension[0]["phases"]["extension"]["inspection"].get("status") != "pass":
        raise RuntimeError("VSIX inspection did not pass")
    packaging = [
        report for report in reports
        if report.get("phases", {}).get("packaging", {}).get("status") == "pass"
    ]
    if len(packaging) != 1:
        raise RuntimeError("exactly one packaging certification report is required")

    warnings = [
        {
            "host_os": report["host_os"],
            "python": report["phases"]["python"]["python"],
            **warning,
        }
        for report in reports
        if "python" in report.get("phases", {})
        for warning in report["phases"]["python"].get("accepted_warnings", [])
    ]
    return reports, warnings


def _validate_gate_reports(input_root: Path, source_commit: str) -> dict[str, Any]:
    release_gates = [
        _load_json(path)
        for path in input_root.rglob("sona-0.15.3-release-gate.json")
    ]
    if len(release_gates) < 6:
        raise RuntimeError("release-gate evidence is missing from the Python matrix")
    for gate in release_gates:
        expected = {
            "schema": 2,
            "positive_pass": 5,
            "negative_pass": 5,
            "fail": 0,
            "warning": 0,
        }
        observed = {key: gate.get(key) for key in expected}
        if gate.get("schema_id") != "sona.release-gate.schema-2" or observed != expected:
            raise RuntimeError(f"invalid release gate counters: {observed}")
        if gate.get("source_commit") != source_commit:
            raise RuntimeError("release gate names the wrong source commit")
        results = gate.get("results", [])
        if (
            len(results) != 10
            or any(result.get("failures") for result in results)
            or any(not all(result.get("checks", {}).values()) for result in results)
            or any(result.get("observed", {}).get("timed_out") for result in results)
        ):
            raise RuntimeError("release gate does not contain ten complete exact matches")
    differentials = [
        _load_json(path)
        for path in input_root.rglob("sona-0.15.3-differential-conformance.json")
    ]
    if len(differentials) < 3:
        raise RuntimeError("differential evidence is missing from the native matrix")
    expected_differential = {
        "fixtures": 20,
        "engine_executions": 40,
        "comparisons": 20,
        "comparison_pass": 20,
        "comparison_fail": 0,
    }
    for report in differentials:
        observed = {key: report.get(key) for key in expected_differential}
        if (
            report.get("schema_id") != "sona.differential-conformance.schema-1"
            or observed != expected_differential
            or report.get("source_commit") != source_commit
        ):
            raise RuntimeError(f"invalid differential conformance report: {observed}")
        results = report.get("results", [])
        if (
            len(results) != 20
            or any(result.get("status") != "pass" for result in results)
            or any(
                not result.get(engine, {}).get("expectation_pass")
                or result.get(engine, {}).get("timed_out")
                for result in results
                for engine in ("python_compat", "native")
            )
        ):
            raise RuntimeError("differential report contains an incomplete comparison")
    standalone = [
        _load_json(path)
        for path in input_root.rglob("sona-0.15.3-native-standalone.json")
    ]
    if len(standalone) < 3:
        raise RuntimeError("native standalone evidence is missing")
    if any(
        report.get("result_counters", {}).get("fail") != 0
        or report.get("source_commit") != source_commit
        or any(result.get("status") != "pass" for result in report.get("results", []))
        or any(result.get("timed_out") for result in report.get("results", []))
        for report in standalone
    ):
        raise RuntimeError("native standalone gate failed or names the wrong commit")
    return {
        "release_gate_reports": len(release_gates),
        "differential_reports": len(differentials),
        "native_standalone_reports": len(standalone),
    }


def _artifact_record(
    path: Path,
    *,
    command: list[str],
    source_commit: str,
    platform_name: str,
    architecture: str,
    inspection: dict[str, Any] | None,
    source_path: str | None = None,
) -> dict[str, Any]:
    return {
        "filename": path.name,
        "source_path": source_path,
        "byte_size": path.stat().st_size,
        "sha256": _sha256(path),
        "producing_command": command,
        "source_commit": source_commit,
        "platform": platform_name,
        "architecture": architecture,
        "archive_inspection": (
            inspection.get("status", "fail") if inspection else "not_applicable"
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Sona {VERSION} Release Certification",
        "",
        f"- Schema: `{report['schema_id']}`",
        f"- Source commit: `{report['source_commit']}`",
        f"- Generated: `{report['generated_at_utc']}`",
        f"- Result: **{report['result']}**",
        "",
        "## Certification matrix",
        "",
        "| OS | Architecture | Python | Phases | Toolchains |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report["certification_matrix"]:
        lines.append(
            f"| {row['host_os']} | {row['architecture']} | "
            f"{row['python']} | {', '.join(row['phases'])} | "
            f"{', '.join(f'{key}={value}' for key, value in row['toolchains'].items())} |"
        )
    lines.extend(
        [
            "",
            "## Published payloads",
            "",
            "| Filename | Bytes | SHA-256 | Archive inspection |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for artifact in report["artifacts"]:
        lines.append(
            f"| {artifact['filename']} | {artifact['byte_size']} | "
            f"`{artifact['sha256']}` | {artifact['archive_inspection']} |"
        )
    lines.extend(
        [
            "",
            "The outer `SHA256SUMS` file is the checksum authority for all release "
            "assets except itself.",
            "",
            "Native Core remains a preview. Python remains the compatibility engine.",
            "PyPI and VS Code Marketplace publication were not performed.",
            "",
        ]
    )
    return "\n".join(lines)


def write_sha256sums(output_root: Path) -> Path:
    checksum = output_root / "SHA256SUMS"
    names = sorted(path.name for path in output_root.iterdir() if path.is_file())
    if checksum.name in names:
        names.remove(checksum.name)
    if set(names) != PUBLISHED_FILES - {"SHA256SUMS"}:
        raise RuntimeError(
            "final asset set is incomplete or contains extras: "
            f"observed={names} expected={sorted(PUBLISHED_FILES - {'SHA256SUMS'})}"
        )
    checksum.write_text(
        "".join(f"{_sha256(output_root / name)}  {name}\n" for name in names),
        encoding="ascii",
        newline="\n",
    )
    return checksum


def verify_sha256sums(output_root: Path) -> None:
    checksum = output_root / "SHA256SUMS"
    lines = checksum.read_text(encoding="ascii").splitlines()
    seen: set[str] = set()
    for line in lines:
        digest, filename = line.split("  ", 1)
        if filename in seen or filename == checksum.name:
            raise RuntimeError(f"invalid SHA256SUMS entry: {filename}")
        seen.add(filename)
        if digest != digest.upper() or digest != _sha256(output_root / filename):
            raise RuntimeError(f"SHA-256 verification failed: {filename}")
    if seen != PUBLISHED_FILES - {"SHA256SUMS"}:
        raise RuntimeError("SHA256SUMS does not cover the exact asset set")


def finalize(
    repository: Path,
    input_root: Path,
    output_root: Path,
) -> Path:
    repository = repository.resolve(strict=True)
    input_root = input_root.resolve(strict=True)
    output_root = require_external_root(repository, output_root)
    if (
        output_root == input_root
        or output_root in input_root.parents
        or input_root in output_root.parents
    ):
        raise RuntimeError("--input-root and --output-root must not overlap")
    clean_repository(repository)
    if any(output_root.iterdir()):
        raise RuntimeError("--output-root must be empty")
    baseline = clone_tree_snapshot(repository)
    source_commit = str(_git(repository, "rev-parse", "HEAD")).strip()
    reports, warnings = _validate_platform_evidence(input_root, source_commit)
    gate_counts = _validate_gate_reports(input_root, source_commit)
    epoch = source_epoch(repository, source_commit)

    wheel = _copy_unique(
        input_root, output_root, f"sona_lang-{VERSION}-py3-none-any.whl"
    )
    sdist = _copy_unique(input_root, output_root, f"sona_lang-{VERSION}.tar.gz")
    vsix = _copy_unique(
        input_root,
        output_root,
        f"sona-ai-native-programming-{VERSION}.vsix",
    )
    windows_binary = _find_unique(
        input_root, f"sona-native-{VERSION}-windows-x86_64.exe"
    )
    linux_binary = _find_unique(
        input_root, f"sona-native-{VERSION}-linux-x86_64-musl"
    )
    windows_archive = output_root / f"sona-native-{VERSION}-windows-x86_64.zip"
    linux_archive = output_root / f"sona-native-{VERSION}-linux-x86_64-musl.tar.gz"
    windows_inspection = build_native_archive(
        windows_binary, windows_archive, archive_kind="windows", epoch=epoch
    )
    linux_inspection = build_native_archive(
        linux_binary, linux_archive, archive_kind="linux", epoch=epoch
    )
    source_archive = output_root / f"sona-{VERSION}-source.tar.gz"
    source_inspection = build_source_archive(
        repository, source_commit, source_archive
    )
    release_notes = output_root / f"RELEASE_NOTES_v{VERSION}.md"
    release_notes.write_bytes(
        _git(
            repository,
            "show",
            f"{source_commit}:RELEASE_NOTES_v{VERSION}.md",
            text=False,
        )
    )
    implementation = output_root / f"{VERSION}-implementation-report.md"
    implementation.write_bytes(
        _git(
            repository,
            "show",
            f"{source_commit}:docs/release/{VERSION}-implementation-report.md",
            text=False,
        )
    )
    assert_clone_unchanged(repository, baseline, "final artifact construction")

    inspections = {
        wheel.name: inspect_archive(wheel, kind="python"),
        sdist.name: inspect_archive(sdist, kind="python"),
        vsix.name: inspect_archive(vsix, kind="vsix"),
        windows_archive.name: windows_inspection,
        linux_archive.name: linux_inspection,
        source_archive.name: source_inspection,
    }
    commands = {
        wheel.name: ["python", "-m", "build", "--outdir", "<cert-root>/artifacts"],
        sdist.name: ["python", "-m", "build", "--outdir", "<cert-root>/artifacts"],
        vsix.name: [
            "npx",
            "--no-install",
            "vsce",
            "package",
            "--out",
            f"<cert-root>/artifacts/{vsix.name}",
        ],
        windows_archive.name: [
            "python",
            "tools/release/artifacts_0153.py",
            "native",
            "--kind",
            "windows",
        ],
        linux_archive.name: [
            "python",
            "tools/release/artifacts_0153.py",
            "native",
            "--kind",
            "linux",
        ],
        source_archive.name: [
            "python",
            "tools/release/artifacts_0153.py",
            "source",
            "--commit",
            source_commit,
        ],
        release_notes.name: ["git", "show", f"{source_commit}:{release_notes.name}"],
        implementation.name: [
            "git",
            "show",
            f"{source_commit}:docs/release/{VERSION}-implementation-report.md",
        ],
    }
    artifact_paths = [
        wheel,
        sdist,
        windows_archive,
        linux_archive,
        vsix,
        source_archive,
        release_notes,
        implementation,
    ]
    artifacts = [
        _artifact_record(
            path,
            command=commands[path.name],
            source_commit=source_commit,
            platform_name=(
                "Windows"
                if path == windows_archive
                else "Linux"
                if path == linux_archive
                else "cross-platform"
            ),
            architecture=(
                "x86_64"
                if path in {windows_archive, linux_archive}
                else "any"
            ),
            inspection=inspections.get(path.name),
            source_path=(
                f"docs/release/{VERSION}-implementation-report.md"
                if path == implementation
                else release_notes.name
                if path == release_notes
                else None
            ),
        )
        for path in artifact_paths
    ]
    matrix = [
        {
            "host_os": report["host_os"],
            "architecture": report["architecture"],
            "python": report["tool_versions"]["python"],
            "phases": sorted(report["phases"]),
            "toolchains": {
                key: value
                for key, value in {
                    "cargo": report.get("phases", {})
                    .get("native", {})
                    .get("cargo"),
                    "rustc": report.get("phases", {})
                    .get("native", {})
                    .get("rustc"),
                    "node": report.get("phases", {})
                    .get("extension", {})
                    .get("node"),
                    "npm": report.get("phases", {})
                    .get("extension", {})
                    .get("npm"),
                }.items()
                if value
            },
        }
        for report in sorted(
            reports,
            key=lambda item: (
                item["host_os"],
                item["tool_versions"]["python"],
                sorted(item["phases"]),
            ),
        )
    ]
    certification = {
        "schema_id": SCHEMA_ID,
        "schema": 1,
        "sona_version": VERSION,
        "source_commit": source_commit,
        "generated_at_utc": _utc_now(),
        "host_operating_system": platform.system(),
        "architecture": platform.machine(),
        "tool_versions": {
            "coordinator_python": platform.python_version(),
            "git": str(_git(repository, "--version")).strip(),
            "certified_platforms": [
                {
                    "host_os": row["host_os"],
                    "architecture": row["architecture"],
                    "python": row["python"],
                    **row["toolchains"],
                }
                for row in matrix
            ],
        },
        "command_summary": [commands[name] for name in sorted(commands)],
        "result_counters": {
            "platform_reports": len(reports),
            "artifact_pass": len(artifacts),
            "fail": 0,
            "warning": len(warnings),
        },
        "artifact_relative_evidence_paths": [
            path.relative_to(input_root).as_posix()
            for path in sorted(input_root.rglob("*.json"))
        ],
        "result": "pass",
        "gate_evidence": gate_counts,
        "accepted_warnings": warnings,
        "certification_matrix": matrix,
        "artifacts": artifacts,
        "authority_files": sorted(AUTHORITY_FILES),
        "published_files": sorted(PUBLISHED_FILES),
        "publication_boundaries": {
            "pypi": "not_performed",
            "vscode_marketplace": "not_performed",
            "native_core": "preview",
            "compatibility_engine": "python",
        },
    }
    json_path = output_root / f"sona-{VERSION}-certification.json"
    markdown_path = output_root / f"sona-{VERSION}-certification.md"
    json_path.write_text(
        json.dumps(certification, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    markdown = render_markdown(certification)
    markdown_path.write_text(markdown, encoding="utf-8", newline="\n")
    if markdown_path.read_text(encoding="utf-8") != render_markdown(
        json.loads(json_path.read_text(encoding="utf-8"))
    ):
        raise RuntimeError("certification Markdown does not match the JSON source")
    write_sha256sums(output_root)
    verify_sha256sums(output_root)
    assert_clone_unchanged(repository, baseline, "final report construction")
    return json_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=ROOT)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    report = finalize(args.repository, args.input_root, args.output_root)
    print(f"Sona {VERSION} final release assets verified: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
