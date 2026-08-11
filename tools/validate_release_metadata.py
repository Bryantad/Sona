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


def tracked_source_maps(root: Path = ROOT) -> list[str]:
    worktree = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    if worktree.returncode == 0 and worktree.stdout.strip() == "true":
        listed = subprocess.run(
            ["git", "ls-files", "*.map"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            check=True,
        ).stdout.splitlines()
        return sorted(path.replace("\\", "/") for path in listed if path)
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*.map")
        if path.is_file()
    )


def validate_dependency_and_toolchain_contracts() -> None:
    pyproject = tomllib.loads(read("pyproject.toml"))
    project = pyproject["project"]
    if project.get("requires-python") != ">=3.11,<3.13":
        fail("pyproject.toml must constrain Python to >=3.11,<3.13")
    if "lark-parser==0.12.0" not in project.get("dependencies", []):
        fail("pyproject.toml must pin lark-parser==0.12.0")
    if read(".nvmrc").strip() != "20.19.5":
        fail(".nvmrc must pin Node 20.19.5")
    toolchain = tomllib.loads(read("rust-toolchain.toml"))
    if toolchain.get("toolchain", {}).get("channel") != "1.94.0":
        fail("rust-toolchain.toml must pin Rust 1.94.0")
    if not (ROOT / "native" / "Cargo.lock").is_file():
        fail("native/Cargo.lock must be committed")

    extension = json.loads(read("vscode-extension/package.json"))
    if extension.get("engines", {}).get("vscode") != "^1.91.0":
        fail("VS Code engine floor must be ^1.91.0")
    if extension.get("dependencies", {}).get("vscode-languageclient") != "10.1.0":
        fail("vscode-languageclient must be pinned to 10.1.0")
    if extension.get("devDependencies", {}).get("@vscode/vsce") != "3.9.2":
        fail("@vscode/vsce must be pinned to 3.9.2")
    if extension.get("devDependencies", {}).get("esbuild") != "0.25.8":
        fail("esbuild must be pinned to 0.25.8")
    security_overrides = extension.get("overrides", {})
    for package, version in {
        "brace-expansion": "5.0.9",
        "minimatch": "10.2.6",
        "cheerio": "1.0.0-rc.12",
        "undici": "7.29.0",
    }.items():
        if security_overrides.get(package) != version:
            fail(f"extension security override must pin {package} {version}")
    lock = json.loads(read("vscode-extension/package-lock.json"))
    root_package = lock.get("packages", {}).get("", {})
    if root_package.get("dependencies", {}).get("vscode-languageclient") != "10.1.0":
        fail("extension lockfile does not pin vscode-languageclient 10.1.0")
    if root_package.get("devDependencies", {}).get("@vscode/vsce") != "3.9.2":
        fail("extension lockfile does not pin @vscode/vsce 3.9.2")
    if root_package.get("devDependencies", {}).get("esbuild") != "0.25.8":
        fail("extension lockfile does not pin esbuild 0.25.8")
    for package, version in {
        "brace-expansion": "5.0.9",
        "minimatch": "10.2.6",
    }.items():
        locked = lock.get("packages", {}).get(f"node_modules/{package}", {})
        if locked.get("version") != version:
            fail(f"extension lockfile does not pin {package} {version}")
    cheerio = lock.get("packages", {}).get(
        "node_modules/@vscode/vsce/node_modules/cheerio",
        {},
    )
    if cheerio.get("version") != "1.0.0-rc.12":
        fail("extension lockfile does not pin VSCE Cheerio 1.0.0-rc.12")
    if any(
        path.endswith("/whatwg-encoding")
        for path in lock.get("packages", {})
    ):
        fail("extension lockfile retains deprecated whatwg-encoding")

    tracked_maps = tracked_source_maps()
    if tracked_maps:
        fail(f"source maps must not be tracked: {', '.join(tracked_maps)}")


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


def parse_native_workspace_version() -> str:
    payload = tomllib.loads(read("native/Cargo.toml"))
    return payload["workspace"]["package"]["version"]


def parse_extension_versions() -> tuple[str, str]:
    package = json.loads(read("vscode-extension/package.json"))
    lock = json.loads(read("vscode-extension/package-lock.json"))
    return package["version"], lock["version"]


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Expected release version")
    args = parser.parse_args()
    expected = args.version
    extension_version, extension_lock_version = parse_extension_versions()

    checks = {
        "pyproject.toml": parse_pyproject_version(),
        "sona/__init__.py": parse_init_version(),
        "sona/cli.py": parse_cli_version_constant(),
        "interpreter __version__": parse_interpreter_version(),
        "sona/stdlib/__init__.py": parse_stdlib_version(),
        "sona/stdlib/MANIFEST.json": parse_manifest_version(),
        "native/Cargo.toml": parse_native_workspace_version(),
        "vscode-extension/package.json": extension_version,
        "vscode-extension/package-lock.json": extension_lock_version,
    }
    for label, value in checks.items():
        if value != expected:
            fail(f"{label} reports {value!r}, expected {expected!r}")

    output = cli_version_output()
    if expected not in output:
        fail(f"CLI version output {output!r} does not contain {expected!r}")

    require_contains("README.md", f"Current release: `{expected}`")
    require_contains("CHANGELOG.md", f"## {expected}")
    for path in (
        "docs/README.md",
        "docs/QUICKSTART.md",
        "docs/LANGUAGE_REFERENCE.md",
        "docs/STDLIB_REFERENCE.md",
        "docs/errors/v0.10-errors.md",
        "docs/errors/v0.14-diagnostics.md",
    ):
        require_contains(path, expected)
    require_contains(f"RELEASE_NOTES_v{expected}.md", f"Sona {expected}")
    require_contains(
        f"docs/release/{expected}-implementation-report.md",
        f"Sona {expected}",
    )
    require_contains("docs/guides/platform-installation-and-testing.md", expected)
    require_contains(".github/workflows/release-platforms-0154.yml", expected)
    for target in (
        "x86_64-unknown-linux-musl",
        "aarch64-unknown-linux-musl",
        "x86_64-apple-darwin",
        "aarch64-apple-darwin",
    ):
        require_contains(".github/workflows/release-platforms-0154.yml", target)
    require_contains("docs/stdlib/catalog.json", f'"version": "{expected}"')
    require_contains("docs/packages/manifest.md", f"v{expected}")
    require_contains(
        "sona/stdlib/MANIFEST.json",
        "0154_stdlib_runtime_capability",
    )
    require_contains(
        "docs/stdlib/catalog.json",
        "0154_stdlib_runtime_capability",
    )
    require_contains("vscode-extension/src/extension.ts", f"Sona {expected} Extension")
    require_contains("vscode-extension/src/sonaCliIntegration.ts", f"Sona {expected}")

    validate_dependency_and_toolchain_contracts()
    print(f"Release metadata validated for {expected}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
