#!/usr/bin/env python3
"""Compatibility runner for the active SMOD/module certification surface."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CERTIFICATION_TESTS = [
    "tests/release/test_015_module_inventory.py",
    "tests/release/test_015_manifest_surface_consistency.py",
    "tests/release/test_015_public_surface_completion.py",
    "tests/test_sona_native_stdlib_0141.py",
    "tests/stdlib/test_utility_modules_015.py",
    "tests/stdlib/test_stable_stdlib_certification_0152.py",
    "tests/accessibility/test_stable_accessibility_modules_015.py",
    "tests/accessibility/test_experimental_accessibility_modules_015.py",
    "tests/regression/test_stdlib_repairs_015.py",
    "tests/modules/test_module_certification_0152.py",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / ".release-artifacts" / "0153-smod-certification",
    )
    args = parser.parse_args(argv)

    command = [sys.executable, "-m", "pytest", "-q", *CERTIFICATION_TESTS]
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        shell=False,
    )
    status = "pass" if proc.returncode == 0 else "fail"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "schema_version": 1,
        "name": "Sona SMOD certification",
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "returncode": proc.returncode,
        "tests": CERTIFICATION_TESTS,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }
    summary_path = args.output_dir / "0153_smod_certification_summary.json"
    report_path = args.output_dir / "0153_smod_certification_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report_path.write_text(
        "\n".join(
            [
                "# Sona SMOD Certification",
                "",
                f"Status: {status}",
                f"Return code: {proc.returncode}",
                "",
                "## Command",
                "",
                f"`{' '.join(command)}`",
                "",
                "## Test files",
                "",
                *[f"- `{item}`" for item in CERTIFICATION_TESTS],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Sona SMOD certification: {status}")
    print(f"Summary: {summary_path}")
    print(f"Report: {report_path}")
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="" if proc.stderr.endswith("\n") else "\n")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
