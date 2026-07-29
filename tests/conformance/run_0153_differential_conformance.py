#!/usr/bin/env python3
"""Run the reviewed bounded cross-engine conformance corpus."""

from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "release"))
from run_0153_release_gate import (  # noqa: E402
    DIAGNOSTIC_RE,
    _deterministic_environment,
    _git_commit,
    _outside_repository,
    _run,
)


SCHEMA_ID = "sona.differential-conformance.schema-1"
SONA_VERSION = "0.15.3"
CLASSIFICATIONS = {
    "identical",
    "shared_diagnostic",
    "unsupported_native",
    "native_only",
}
NATIVE_DIAGNOSTIC_RE = re.compile(
    r"\Aerror\[(?P<e_code>[^\]]+)\] (?P<diagnostic_id>[^:]+): "
    r"(?P<primary_message>[^\n]*)\n"
    r"  --> (?P<file>.+):(?P<line>\d+):(?P<column>\d+)\n"
    r"  hint: (?P<hint>[^\n]*)\n\Z"
)


@dataclass(frozen=True)
class EngineExecution:
    engine: str
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool
    expectation_pass: bool


@dataclass(frozen=True)
class Comparison:
    name: str
    source: str
    classification: str
    status: str
    parity_claim: bool
    python_compat: EngineExecution
    native: EngineExecution
    normalized_python: dict[str, Any]
    normalized_native: dict[str, Any]


def _load_fixtures() -> list[dict[str, Any]]:
    fixtures = []
    for sidecar in sorted((ROOT / "tests" / "conformance").glob("*/*.expected.json")):
        fixture = json.loads(sidecar.read_text(encoding="utf-8"))
        if fixture.get("schema") != 1:
            raise ValueError(f"{sidecar}: unsupported fixture schema")
        if fixture.get("classification") not in CLASSIFICATIONS:
            raise ValueError(f"{sidecar}: invalid classification")
        if set(fixture.get("expected", {})) != {"python-compat", "native"}:
            raise ValueError(f"{sidecar}: both engine expectations are required")
        for engine in ("python-compat", "native"):
            if set(fixture["expected"][engine]) != {"exit_code", "stdout", "stderr"}:
                raise ValueError(f"{sidecar}: {engine} expectation fields are not exact")
        source = ROOT / fixture["source"]
        if not source.is_file():
            raise ValueError(f"{sidecar}: source is missing")
        fixtures.append(fixture)
    if len(fixtures) != 20:
        raise ValueError(f"exactly 20 reviewed fixtures are required; found {len(fixtures)}")
    return fixtures


def _execute(
    fixture: dict[str, Any],
    engine: str,
    native_binary: Path,
) -> EngineExecution:
    if engine == "python-compat":
        command = [
            sys.executable,
            "-m",
            "sona",
            "run",
            fixture["source"],
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
            fixture["source"],
            "--engine",
            "native",
        ]
        recorded = ["<native>", *command[1:]]
    completed = _run(
        command,
        int(fixture["timeout_seconds"]),
        env=_deterministic_environment(),
    )
    expected = fixture["expected"][engine]
    passed = (
        not completed.timed_out
        and completed.returncode == expected["exit_code"]
        and completed.stdout == expected["stdout"]
        and completed.stderr == expected["stderr"]
    )
    return EngineExecution(
        engine=engine,
        command=recorded,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        timed_out=completed.timed_out,
        expectation_pass=passed,
    )


def _diagnostic_projection(stderr: str, engine: str) -> dict[str, Any] | None:
    pattern = DIAGNOSTIC_RE if engine == "python-compat" else NATIVE_DIAGNOSTIC_RE
    match = pattern.fullmatch(stderr)
    if match is None:
        return None
    projection: dict[str, Any] = match.groupdict()
    projection.pop("exception", None)
    projection["line"] = int(projection["line"])
    projection["column"] = int(projection["column"])
    return projection


def _normalized(execution: EngineExecution) -> dict[str, Any]:
    if execution.exit_code == 0:
        return {
            "status": "success",
            "stdout": execution.stdout,
            "stderr": execution.stderr,
        }
    diagnostic = _diagnostic_projection(execution.stderr, execution.engine)
    if diagnostic is not None:
        return {"status": "diagnostic", **diagnostic}
    return {
        "status": "failure",
        "exit_code": execution.exit_code,
        "stdout": execution.stdout,
        "stderr": execution.stderr,
    }


def _compare(fixture: dict[str, Any], native_binary: Path) -> Comparison:
    python_result = _execute(fixture, "python-compat", native_binary)
    native_result = _execute(fixture, "native", native_binary)
    normalized_python = _normalized(python_result)
    normalized_native = _normalized(native_result)
    classification = fixture["classification"]
    expectations_pass = (
        python_result.expectation_pass and native_result.expectation_pass
    )
    if classification in {"identical", "shared_diagnostic"}:
        comparison_pass = expectations_pass and normalized_python == normalized_native
        parity_claim = comparison_pass
    else:
        # The pair is reviewed and counted as bounded conformance, but never as
        # semantic parity when one engine is intentionally outside its subset.
        comparison_pass = expectations_pass
        parity_claim = False
    return Comparison(
        name=fixture["name"],
        source=fixture["source"],
        classification=classification,
        status="pass" if comparison_pass else "fail",
        parity_claim=parity_claim,
        python_compat=python_result,
        native=native_result,
        normalized_python=normalized_python,
        normalized_native=normalized_native,
    )


def _write_markdown(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Sona 0.15.3 Differential Conformance",
        "",
        "This is bounded cross-engine conformance, not full semantic parity.",
        "",
        f"- Schema: `{summary['schema_id']}`",
        f"- Fixtures: {summary['fixtures']}",
        f"- Engine executions: {summary['engine_executions']}",
        f"- Comparisons: {summary['comparisons']}",
        f"- Comparison pass: {summary['comparison_pass']}",
        f"- Comparison fail: {summary['comparison_fail']}",
        "",
        "| Fixture | Classification | Result | Parity claim |",
        "| --- | --- | --- | --- |",
    ]
    for comparison in summary["results"]:
        lines.append(
            f"| {comparison['name']} | {comparison['classification']} | "
            f"{comparison['status']} | {str(comparison['parity_claim']).lower()} |"
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

    results = [_compare(fixture, native_binary) for fixture in _load_fixtures()]
    comparison_pass = sum(result.status == "pass" for result in results)
    comparison_fail = sum(result.status == "fail" for result in results)
    engine_executions = len(results) * 2
    json_path = output_dir / "sona-0.15.3-differential-conformance.json"
    markdown_path = output_dir / "sona-0.15.3-differential-conformance.md"
    summary = {
        "schema_id": SCHEMA_ID,
        "schema": 1,
        "sona_version": SONA_VERSION,
        "source_commit": _git_commit(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "host_os": platform.system(),
        "architecture": platform.machine(),
        "tool_versions": {
            "python": platform.python_version(),
            "native_core": SONA_VERSION,
        },
        "command_summary": [
            execution.command
            for result in results
            for execution in (result.python_compat, result.native)
        ],
        "artifact_relative_evidence_paths": [json_path.name, markdown_path.name],
        "scope": "bounded cross-engine conformance",
        "fixtures": len(results),
        "engine_executions": engine_executions,
        "comparisons": len(results),
        "comparison_pass": comparison_pass,
        "comparison_fail": comparison_fail,
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
        raise RuntimeError(
            "differential-conformance Markdown does not match its JSON source"
        )
    print(
        "Sona 0.15.3 differential conformance: "
        f"{'pass' if comparison_fail == 0 else 'fail'}"
    )
    print(f"JSON: {json_path}")
    print(f"Markdown: {markdown_path}")
    print(
        f"Counts: fixtures={len(results)} engine_executions={engine_executions} "
        f"comparisons={len(results)} comparison_pass={comparison_pass} "
        f"comparison_fail={comparison_fail}"
    )
    return (
        0
        if len(results) == 20
        and engine_executions == 40
        and comparison_pass == 20
        and comparison_fail == 0
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
