#!/usr/bin/env python3
"""Validate public release metadata consistency."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[1]

ACTIVE_STALE_SCAN = [
    "README.md",
    "CHANGELOG.md",
    "RELEASE_NOTES_v0.15.0.md",
    "pyproject.toml",
    "sona/__init__.py",
    "sona/cli.py",
    "sona/interpreter.py",
    "sona/lsp_server.py",
    "sona/spm.py",
    "sona/stdlib/__init__.py",
    "sona/stdlib/MANIFEST.json",
    "docs/README.md",
    "docs/QUICKSTART.md",
    "docs/LANGUAGE_REFERENCE.md",
    "docs/STDLIB_REFERENCE.md",
    "docs/errors/v0.10-errors.md",
    "docs/errors/v0.14-diagnostics.md",
    "docs/packages/manifest.md",
    "docs/stdlib/catalog.json",
    "scripts/release_gate.ps1",
    "scripts/release_hardening.ps1",
    "tools/run_examples.py",
]


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require_contains(path: str, needle: str) -> None:
    if needle not in read(path):
        fail(f"{path} does not contain {needle!r}")


def parse_pyproject_version() -> str:
    payload = tomllib.loads(read("pyproject.toml"))
    return payload["project"]["version"]


def parse_init_version() -> str:
    text = read("sona/__init__.py")
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        fail("sona/__init__.py missing __version__")
    return match.group(1)


def parse_cli_version_constant() -> str:
    text = read("sona/cli.py")
    match = re.search(r'^SONA_VERSION\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        fail("sona/cli.py missing SONA_VERSION")
    return match.group(1)


def parse_interpreter_version() -> str:
    text = read("sona/interpreter.py")
    match = re.search(r"set_variable\('__version__', '([^']+)'", text)
    if not match:
        fail("sona/interpreter.py missing interpreter __version__ global")
    return match.group(1)


def parse_stdlib_version() -> str:
    text = read("sona/stdlib/__init__.py")
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        fail("sona/stdlib/__init__.py missing __version__")
    return match.group(1)


def parse_manifest_version() -> str:
    payload = json.loads(read("sona/stdlib/MANIFEST.json"))
    return payload["version"]


def parse_release_script_default(path: str) -> str:
    text = read(path)
    match = re.search(r'\[string\]\$ExpectedVersion\s*=\s*"([^"]+)"', text)
    if not match:
        fail(f"{path} missing ExpectedVersion default")
    return match.group(1)


def cli_version_output() -> str:
    proc = subprocess.run(
        [sys.executable, "-m", "sona", "--version"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        fail(proc.stderr or proc.stdout or "python -m sona --version failed")
    return proc.stdout.strip()


def check_no_stale_active_references(version: str) -> None:
    stale = "0.14.1"
    for path in ACTIVE_STALE_SCAN:
        text = read(path)
        if path != "CHANGELOG.md" and stale in text:
            fail(f"active file {path} still contains stale {stale}")
        if path not in {"CHANGELOG.md"} and version not in text:
            fail(f"active file {path} does not contain expected version {version}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Expected release version")
    args = parser.parse_args()
    expected = args.version

    checks = {
        "pyproject.toml": parse_pyproject_version(),
        "sona/__init__.py": parse_init_version(),
        "sona/cli.py": parse_cli_version_constant(),
        "interpreter __version__": parse_interpreter_version(),
        "sona/stdlib/__init__.py": parse_stdlib_version(),
        "sona/stdlib/MANIFEST.json": parse_manifest_version(),
        "scripts/release_gate.ps1": parse_release_script_default("scripts/release_gate.ps1"),
        "scripts/release_hardening.ps1": parse_release_script_default("scripts/release_hardening.ps1"),
    }
    for label, value in checks.items():
        if value != expected:
            fail(f"{label} reports {value!r}, expected {expected!r}")

    output = cli_version_output()
    if expected not in output:
        fail(f"CLI version output {output!r} does not contain {expected!r}")

    require_contains("README.md", f"Current release: `{expected}`")
    require_contains("CHANGELOG.md", f"## {expected}")
    require_contains(f"RELEASE_NOTES_v{expected}.md", f"Sona {expected}")
    require_contains("docs/stdlib/catalog.json", f'"version": "{expected}"')
    require_contains("docs/packages/manifest.md", f"v{expected}")
    require_contains("sona/stdlib/MANIFEST.json", "0150_cognitive_runtime_guardian")

    check_no_stale_active_references(expected)
    print(f"Release metadata validated for {expected}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
