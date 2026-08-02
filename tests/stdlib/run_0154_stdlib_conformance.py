#!/usr/bin/env python3
"""Run the reviewed bounded Sona 0.15.4 stdlib cross-engine corpus."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = ROOT / "tests" / "stdlib" / "conformance"
SCHEMA_ID = "sona.stdlib-conformance.schema-1"


@dataclass(frozen=True)
class Execution:
    engine: str
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool
    expectation_pass: bool


def _outside_repository(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT.resolve())
        return False
    except ValueError:
        return True


def _environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment.update(
        {
            "NO_COLOR": "1",
            "FORCE_COLOR": "0",
            "PYTHONUTF8": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(ROOT),
        }
    )
    return environment


def _run(
    command: list[str],
    *,
    cwd: Path,
    stdin_text: str,
    timeout: int = 30,
) -> tuple[int, str, str, bool]:
    kwargs: dict[str, Any] = {
        "cwd": cwd,
        "env": _environment(),
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "stdin": subprocess.PIPE,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "shell": False,
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    process = subprocess.Popen(command, **kwargs)
    try:
        stdout, stderr = process.communicate(input=stdin_text, timeout=timeout)
        return process.returncode, _normalize(stdout), _normalize(stderr), False
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            process.send_signal(signal.CTRL_BREAK_EVENT)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
        else:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
        return process.returncode or 124, _normalize(stdout), _normalize(stderr), True


def _normalize(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _execute(
    fixture: dict[str, Any],
    engine: str,
    native_binary: Path,
    work_root: Path,
) -> Execution:
    workdir = work_root / fixture["name"] / engine
    workdir.mkdir(parents=True, exist_ok=True)
    source = workdir / "fixture.sona"
    shutil.copy2(FIXTURE_ROOT / fixture["source"], source)
    if engine == "python-compat":
        command = [
            sys.executable,
            "-m",
            "sona",
            "run",
            str(source),
            "--compatibility",
            "sona",
            "--errors",
            "explain",
            "--types",
            "off",
            "--types-log",
            "silent",
        ]
        recorded = ["<python>", *command[1:]]
    else:
        command = [
            str(native_binary),
            "run",
            str(source),
            "--engine",
            "native",
            *fixture.get("native_capabilities", []),
        ]
        recorded = ["<native>", *command[1:]]
    exit_code, stdout, stderr, timed_out = _run(
        command,
        cwd=workdir,
        stdin_text=fixture["stdin"],
    )
    passed = (
        not timed_out
        and exit_code == 0
        and stdout == fixture["stdout"]
        and stderr == ""
    )
    return Execution(
        engine=engine,
        command=recorded,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
        expectation_pass=passed,
    )


def _git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
        timeout=10,
    ).stdout.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-binary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    native_binary = args.native_binary.resolve()
    output_dir = args.output_dir.resolve()
    if not native_binary.is_file():
        parser.error("--native-binary must name an existing binary")
    if not _outside_repository(output_dir):
        parser.error("--output-dir must resolve outside the repository")
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((FIXTURE_ROOT / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_id") != "sona.stdlib-conformance-fixtures.schema-1":
        raise ValueError("invalid stdlib fixture manifest")
    fixtures = manifest["fixtures"]
    if len(fixtures) != 10 or len({item["module"] for item in fixtures}) != 10:
        raise ValueError("exactly ten distinct supported-module fixtures are required")

    results = []
    work_root = output_dir / "work"
    for fixture in fixtures:
        python_result = _execute(fixture, "python-compat", native_binary, work_root)
        native_result = _execute(fixture, "native", native_binary, work_root)
        status = (
            "pass"
            if python_result.expectation_pass
            and native_result.expectation_pass
            and python_result.stdout == native_result.stdout
            else "fail"
        )
        results.append(
            {
                "name": fixture["name"],
                "module": fixture["module"],
                "classification": fixture["classification"],
                "status": status,
                "python_compat": asdict(python_result),
                "native": asdict(native_result),
            }
        )

    passed = sum(item["status"] == "pass" for item in results)
    failed = len(results) - passed
    report = {
        "schema": 1,
        "schema_id": SCHEMA_ID,
        "sona_version": "0.15.4",
        "source_commit": _git_commit(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "host_os": platform.system(),
        "architecture": platform.machine(),
        "tool_versions": {"python": platform.python_version()},
        "command_summary": [
            execution["command"]
            for item in results
            for execution in (item["python_compat"], item["native"])
        ],
        "artifact_relative_evidence_paths": ["sona-0.15.4-stdlib-conformance.json"],
        "scope": "bounded standard-library conformance, not full semantic parity",
        "fixtures": len(results),
        "engine_executions": len(results) * 2,
        "comparisons": len(results),
        "comparison_pass": passed,
        "comparison_fail": failed,
        "excluded": manifest["excluded"],
        "results": results,
    }
    report_path = output_dir / "sona-0.15.4-stdlib-conformance.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"Sona 0.15.4 stdlib conformance: fixtures={len(results)} "
        f"executions={len(results) * 2} pass={passed} fail={failed}"
    )
    print(f"JSON: {report_path}")
    return 0 if passed == 10 and failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
