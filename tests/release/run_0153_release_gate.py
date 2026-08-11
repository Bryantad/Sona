#!/usr/bin/env python3
"""Exact positive and negative conformance gate for the active Sona release."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import platform
import re
import signal
import subprocess
import sys
import tomllib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ID = "sona.release-gate.schema-2"
SONA_VERSION = str(
    tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
)
CASES_DIR = Path(__file__).with_name("cases")
ANSI_RE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
DIAGNOSTIC_RE = re.compile(
    r"\A(?P<exception>[A-Za-z_][A-Za-z0-9_]*): "
    r"(?P<diagnostic_id>[^:]+): error\[(?P<e_code>[^\]]+)\]: "
    r"(?P<primary_message>[^\n]*)\n"
    r"  at (?P<file>.+):(?P<line>\d+):(?P<column>\d+)\n"
    r"  hint: (?P<hint>[^\n]*)\n\Z"
)
HOST_EXCEPTION_RE = re.compile(
    r"(?m)^(?:AttributeError|TypeError|ValueError|KeyError|IndexError|"
    r"AssertionError|OSError|RuntimeError|SyntaxError):"
)
EXPECTED_FIELDS = {
    "exit_code",
    "exception_classification",
    "diagnostic_id",
    "e_code",
    "primary_message",
    "file",
    "line",
    "column",
    "hint",
    "stdout",
    "stderr",
    "ansi",
    "traceback",
    "host_exception",
    "rust_panic",
    "unrelated_log",
}


@dataclass(frozen=True)
class Completed:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    process_count: int | None


@dataclass(frozen=True)
class CaseResult:
    name: str
    kind: str
    status: str
    execution_mode: str
    command: list[str]
    timeout_seconds: int
    observed: dict[str, Any]
    checks: dict[str, bool]
    failures: list[str]


class _WindowsJob:
    """Kill an entire Windows subprocess tree when the bounded timeout expires."""

    def __init__(self, process: subprocess.Popen[str]) -> None:
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._kernel32.CreateJobObjectW.restype = ctypes.c_void_p
        self._kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
        self._kernel32.SetInformationJobObject.restype = ctypes.c_int
        self._kernel32.QueryInformationJobObject.restype = ctypes.c_int
        self._kernel32.AssignProcessToJobObject.restype = ctypes.c_int
        self._kernel32.TerminateJobObject.restype = ctypes.c_int
        self._kernel32.CloseHandle.restype = ctypes.c_int
        self._handle = self._kernel32.CreateJobObjectW(None, None)
        if not self._handle:
            raise ctypes.WinError(ctypes.get_last_error())

        class IoCounters(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_ulonglong),
                ("WriteOperationCount", ctypes.c_ulonglong),
                ("OtherOperationCount", ctypes.c_ulonglong),
                ("ReadTransferCount", ctypes.c_ulonglong),
                ("WriteTransferCount", ctypes.c_ulonglong),
                ("OtherTransferCount", ctypes.c_ulonglong),
            ]

        class BasicLimits(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_longlong),
                ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", ctypes.c_uint32),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", ctypes.c_uint32),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", ctypes.c_uint32),
                ("SchedulingClass", ctypes.c_uint32),
            ]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", BasicLimits),
                ("IoInfo", IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        class BasicAccounting(ctypes.Structure):
            _fields_ = [
                ("TotalUserTime", ctypes.c_longlong),
                ("TotalKernelTime", ctypes.c_longlong),
                ("ThisPeriodTotalUserTime", ctypes.c_longlong),
                ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
                ("TotalPageFaultCount", ctypes.c_uint32),
                ("TotalProcesses", ctypes.c_uint32),
                ("ActiveProcesses", ctypes.c_uint32),
                ("TotalTerminatedProcesses", ctypes.c_uint32),
            ]

        self._basic_accounting = BasicAccounting
        limits = ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x00002000
        if not self._kernel32.SetInformationJobObject(
            self._handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)
        ):
            self.close()
            raise ctypes.WinError(ctypes.get_last_error())
        if not self._kernel32.AssignProcessToJobObject(
            self._handle, ctypes.c_void_p(process._handle)
        ):
            self.close()
            raise ctypes.WinError(ctypes.get_last_error())

    def terminate(self) -> None:
        if self._handle:
            self._kernel32.TerminateJobObject(self._handle, 124)

    def process_count(self) -> int:
        accounting = self._basic_accounting()
        if not self._kernel32.QueryInformationJobObject(
            self._handle,
            1,
            ctypes.byref(accounting),
            ctypes.sizeof(accounting),
            None,
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        return int(accounting.TotalProcesses)

    def close(self) -> None:
        if self._handle:
            self._kernel32.CloseHandle(self._handle)
            self._handle = None


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _deterministic_environment() -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("SONA_")
    }
    environment.update(
        {
            "NO_COLOR": "1",
            "FORCE_COLOR": "0",
            "PYTHONUTF8": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    return environment


def _run(
    command: list[str],
    timeout_seconds: int,
    *,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
) -> Completed:
    kwargs: dict[str, Any] = {
        "cwd": cwd,
        "env": env,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "shell": False,
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    process = subprocess.Popen(command, **kwargs)
    job = _WindowsJob(process) if os.name == "nt" else None
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
        return Completed(
            process.returncode,
            _normalize(stdout),
            _normalize(stderr),
            False,
            job.process_count() if job is not None else None,
        )
    except subprocess.TimeoutExpired:
        if job is not None:
            job.terminate()
        else:
            os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            if job is not None:
                job.terminate()
            else:
                os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
        return Completed(
            process.returncode if process.returncode is not None else 124,
            _normalize(stdout),
            _normalize(stderr),
            True,
            job.process_count() if job is not None else None,
        )
    finally:
        if job is not None:
            job.close()


def _diagnostic(stderr: str) -> dict[str, Any]:
    match = DIAGNOSTIC_RE.fullmatch(stderr)
    if match is None:
        return {
            "exception_classification": None,
            "diagnostic_id": None,
            "e_code": None,
            "primary_message": None,
            "file": None,
            "line": None,
            "column": None,
            "hint": None,
        }
    parsed: dict[str, Any] = match.groupdict()
    parsed["exception_classification"] = parsed.pop("exception")
    parsed["line"] = int(parsed["line"])
    parsed["column"] = int(parsed["column"])
    return parsed


def _load_cases() -> list[dict[str, Any]]:
    cases = []
    for sidecar in sorted(CASES_DIR.glob("*.expected.json")):
        case = json.loads(sidecar.read_text(encoding="utf-8"))
        if case.get("schema") != 1:
            raise ValueError(f"{sidecar}: unsupported sidecar schema")
        if set(case.get("expected", {})) != EXPECTED_FIELDS:
            raise ValueError(f"{sidecar}: expectation fields are not exact")
        source = ROOT / case["source"]
        if not source.is_file():
            raise ValueError(f"{sidecar}: source is missing")
        cases.append(case)
    positives = sum(case["kind"] == "positive" for case in cases)
    negatives = sum(case["kind"] == "negative" for case in cases)
    if len(cases) != 10 or positives != 5 or negatives != 5:
        raise ValueError("release gate requires exactly five positive and five negative cases")
    return cases


def _evaluate(case: dict[str, Any]) -> CaseResult:
    command = [
        sys.executable,
        "-m",
        "sona",
        "run",
        case["source"],
        "--compatibility",
        "sona",
        "--errors",
        "explain",
        "--types",
        "off",
        "--types-log",
        "silent",
    ]
    timeout_seconds = int(case["timeout_seconds"])
    completed = _run(
        command,
        timeout_seconds,
        env=_deterministic_environment(),
    )
    diagnostic = _diagnostic(completed.stderr)
    observed = {
        "exit_code": completed.returncode,
        **diagnostic,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "ansi": bool(ANSI_RE.search(completed.stdout + completed.stderr)),
        "traceback": "Traceback (most recent call last):" in completed.stderr,
        "host_exception": bool(HOST_EXCEPTION_RE.search(completed.stderr)),
        "rust_panic": (
            "panicked at" in completed.stderr
            or "thread '" in completed.stderr
            and "panic" in completed.stderr.lower()
        ),
        "unrelated_log": False,
        "timed_out": completed.timed_out,
    }
    expected = case["expected"]
    observed["unrelated_log"] = (
        observed["stdout"] != expected["stdout"]
        or observed["stderr"] != expected["stderr"]
    )
    checks = {
        field: observed[field] == expected[field]
        for field in sorted(EXPECTED_FIELDS)
    }
    checks["execution_mode"] = case["execution_mode"] == "python-compat"
    checks["timeout"] = not completed.timed_out
    failures = [name for name, passed in checks.items() if not passed]
    if not failures:
        status = "positive_pass" if case["kind"] == "positive" else "negative_pass"
    else:
        status = "fail"
    return CaseResult(
        name=case["name"],
        kind=case["kind"],
        status=status,
        execution_mode=case["execution_mode"],
        command=["<python>", *command[1:]],
        timeout_seconds=timeout_seconds,
        observed=observed,
        checks=checks,
        failures=failures,
    )


def _git_commit() -> str:
    injected = os.environ.get("SONA_SOURCE_COMMIT", "").strip()
    if injected:
        if re.fullmatch(r"[0-9a-fA-F]{40}", injected) is None:
            raise ValueError("SONA_SOURCE_COMMIT must be a full 40-character Git SHA")
        return injected.lower()
    process = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        shell=False,
        check=True,
    )
    return process.stdout.strip()


def _write_markdown(summary: dict[str, Any], path: Path) -> None:
    lines = [
        f"# Sona {SONA_VERSION} Release Gate",
        "",
        f"- Schema: `{summary['schema_id']}`",
        f"- Source commit: `{summary['source_commit']}`",
        f"- Positive pass: {summary['positive_pass']}",
        f"- Negative pass: {summary['negative_pass']}",
        f"- Fail: {summary['fail']}",
        f"- Warning: {summary['warning']}",
        "",
        "| Case | Kind | Result | Exit |",
        "| --- | --- | --- | ---: |",
    ]
    for result in summary["results"]:
        lines.append(
            f"| {result['name']} | {result['kind']} | {result['status']} | "
            f"{result['observed']['exit_code']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _outside_repository(path: Path) -> bool:
    resolved = path.resolve()
    repository = ROOT.resolve()
    return resolved != repository and repository not in resolved.parents


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    output_dir = args.output_dir.resolve()
    if not _outside_repository(output_dir):
        parser.error("--output-dir must resolve outside the repository")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = [_evaluate(case) for case in _load_cases()]
    positive_pass = sum(result.status == "positive_pass" for result in results)
    negative_pass = sum(result.status == "negative_pass" for result in results)
    failures = sum(result.status == "fail" for result in results)
    json_path = output_dir / f"sona-{SONA_VERSION}-release-gate.json"
    markdown_path = output_dir / f"sona-{SONA_VERSION}-release-gate.md"
    summary = {
        "schema_id": SCHEMA_ID,
        "schema": 2,
        "sona_version": SONA_VERSION,
        "source_commit": _git_commit(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "host_os": platform.system(),
        "architecture": platform.machine(),
        "tool_versions": {
            "python": platform.python_version(),
            "lark_parser": __import__("lark").__version__,
        },
        "command_summary": [result.command for result in results],
        "artifact_relative_evidence_paths": [json_path.name, markdown_path.name],
        "positive_pass": positive_pass,
        "negative_pass": negative_pass,
        "fail": failures,
        "warning": 0,
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
        raise RuntimeError("release-gate Markdown does not match its JSON source")
    print(f"Sona {SONA_VERSION} release gate: {'pass' if failures == 0 else 'fail'}")
    print(f"JSON: {json_path}")
    print(f"Markdown: {markdown_path}")
    print(
        "Counts: "
        f"positive_pass={positive_pass} negative_pass={negative_pass} "
        f"fail={failures} warning=0"
    )
    return 0 if positive_pass == 5 and negative_pass == 5 and failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
