#!/usr/bin/env python3
"""Run the Windows/Linux Native Core standalone evidence gate."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_0153_release_gate import _git_commit, _outside_repository, _run  # noqa: E402


SCHEMA_ID = "sona.native-standalone.schema-1"
SONA_VERSION = "0.15.3"


@dataclass(frozen=True)
class GateResult:
    name: str
    status: str
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool
    process_count: int | None


def _isolated_environment(bin_dir: Path, empty_path: Path) -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("PYTHON")
        and not key.upper().startswith("SONA_")
    }
    environment["PATH"] = os.pathsep.join((str(bin_dir), str(empty_path)))
    environment["SONA_ENGINE"] = "native"
    environment["SONA_NATIVE_STANDALONE"] = "1"
    return environment


def _case(
    name: str,
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    stdout: str,
    stderr: str = "",
) -> GateResult:
    completed = _run(command, 30, cwd=cwd, env=environment)
    passed = (
        not completed.timed_out
        and completed.returncode == 0
        and completed.stdout == stdout
        and completed.stderr == stderr
        and "Traceback (most recent call last):" not in completed.stderr
        and "panicked at" not in completed.stderr
        and (os.name != "nt" or completed.process_count == 1)
    )
    return GateResult(
        name=name,
        status="pass" if passed else "fail",
        command=["<native>", *command[1:]],
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        timed_out=completed.timed_out,
        process_count=completed.process_count,
    )


def _write_markdown(summary: dict, path: Path) -> None:
    lines = [
        "# Sona 0.15.3 Native Standalone Gate",
        "",
        f"- Schema: `{summary['schema_id']}`",
        f"- Source commit: `{summary['source_commit']}`",
        f"- Pass: {summary['result_counters']['pass']}",
        f"- Fail: {summary['result_counters']['fail']}",
        "",
        "| Case | Result | Exit |",
        "| --- | --- | ---: |",
    ]
    for result in summary["results"]:
        lines.append(
            f"| {result['name']} | {result['status']} | {result['exit_code']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-binary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    native_binary = args.native_binary.resolve()
    output_dir = args.output_dir.resolve()
    if not native_binary.is_file():
        parser.error("--native-binary must name an existing release binary")
    if not _outside_repository(output_dir):
        parser.error("--output-dir must resolve outside the repository")
    output_dir.mkdir(parents=True, exist_ok=True)

    isolated_root = output_dir / "isolated"
    if isolated_root.exists():
        shutil.rmtree(isolated_root)
    bin_dir = isolated_root / "bin"
    programs_dir = isolated_root / "programs"
    empty_path = isolated_root / "empty-path"
    for directory in (bin_dir, programs_dir, empty_path):
        directory.mkdir(parents=True, exist_ok=True)
    isolated_binary = bin_dir / native_binary.name
    shutil.copy2(native_binary, isolated_binary)
    for item in sorted((ROOT / "native" / "tests" / "conformance").iterdir()):
        if item.suffix in {".sona", ".smod"}:
            shutil.copy2(item, programs_dir / item.name)

    environment = _isolated_environment(bin_dir, empty_path)
    results: list[GateResult] = []
    for executable in ("python", "python3", "py"):
        found = shutil.which(executable, path=environment["PATH"])
        results.append(
            GateResult(
                name=f"no-{executable}-on-path",
                status="pass" if found is None else "fail",
                command=[executable, "--version"],
                exit_code=0 if found is None else 1,
                stdout="",
                stderr=found or "",
                timed_out=False,
                process_count=None,
            )
        )

    binary = str(isolated_binary)
    doctor = (
        "native_binary_version=0.15.3\n"
        "bytecode_version=1\n"
        "feature_level=Sona Native Core preview\n"
        "python_required=false\n"
        "python_embedded=false\n"
        "default_capabilities=console:allow,filesystem:deny,network:deny,"
        "process:deny,environment:deny\n"
        "modules=smod-preview\n"
    )
    cases = [
        ("doctor-native", [binary, "doctor", "native"], doctor),
        (
            "hello",
            [binary, "run", str(programs_dir / "hello.sona"), "--engine", "native"],
            "Hello from native Sona\n",
        ),
        (
            "arithmetic",
            [binary, "run", str(programs_dir / "arithmetic.sona"), "--engine", "native"],
            "14\nhello5\n6\n",
        ),
        (
            "functions",
            [binary, "run", str(programs_dir / "functions.sona"), "--engine", "native"],
            "12\n",
        ),
        (
            "control-flow",
            [
                binary,
                "run",
                str(programs_dir / "control_flow.sona"),
                "--engine",
                "native",
            ],
            "ok\n",
        ),
        (
            "module-import",
            [
                binary,
                "run",
                str(programs_dir / "module_import.sona"),
                "--engine",
                "native",
            ],
            "42\n",
        ),
        (
            "check",
            [
                binary,
                "check",
                str(programs_dir / "functions.sona"),
                "--engine",
                "native",
            ],
            "ok\n",
        ),
    ]
    for name, command, expected_stdout in cases:
        results.append(
            _case(
                name,
                command,
                cwd=isolated_root,
                environment=environment,
                stdout=expected_stdout,
            )
        )

    container = isolated_root / "hello.sbc"
    results.append(
        _case(
            "compile-container",
            [
                binary,
                "compile",
                str(programs_dir / "hello.sona"),
                "--output",
                str(container),
            ],
            cwd=isolated_root,
            environment=environment,
            stdout=f"{container}\n",
        )
    )
    results.append(
        _case(
            "execute-container",
            [binary, "exec", str(container)],
            cwd=isolated_root,
            environment=environment,
            stdout="Hello from native Sona\n",
        )
    )

    passed = sum(result.status == "pass" for result in results)
    failed = sum(result.status == "fail" for result in results)
    json_path = output_dir / "sona-0.15.3-native-standalone.json"
    markdown_path = output_dir / "sona-0.15.3-native-standalone.md"
    summary = {
        "schema_id": SCHEMA_ID,
        "schema": 1,
        "sona_version": SONA_VERSION,
        "source_commit": _git_commit(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "host_os": platform.system(),
        "architecture": platform.machine(),
        "tool_versions": {
            "python_harness": platform.python_version(),
            "native_core": SONA_VERSION,
        },
        "command_summary": [result.command for result in results],
        "artifact_relative_evidence_paths": [json_path.name, markdown_path.name],
        "python_removed_from_child_path": all(
            result.status == "pass"
            for result in results
            if result.name.startswith("no-")
        ),
        "result_counters": {"pass": passed, "fail": failed},
        "results": [asdict(result) for result in results],
    }
    json_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    _write_markdown(summary, markdown_path)
    rendered = markdown_path.read_text(encoding="utf-8")
    _write_markdown(
        json.loads(json_path.read_text(encoding="utf-8")),
        markdown_path,
    )
    if markdown_path.read_text(encoding="utf-8") != rendered:
        raise RuntimeError("native-standalone Markdown does not match its JSON source")
    print(f"Sona Native Standalone Gate: {'pass' if failed == 0 else 'fail'}")
    print(f"JSON: {json_path}")
    print(f"Markdown: {markdown_path}")
    print(f"Counts: pass={passed} fail={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
