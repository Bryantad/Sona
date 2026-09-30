#!/usr/bin/env python3
"""Build and verify Sona 0.16.0 release candidates using the shared platform pipeline."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


_implementation_name = "sona_platform_release_0160_impl"
_implementation_path = Path(__file__).with_name("platform_release_0156.py")
_implementation_spec = importlib.util.spec_from_file_location(
    _implementation_name, _implementation_path
)
if _implementation_spec is None or _implementation_spec.loader is None:
    raise RuntimeError("Could not load the shared platform release implementation.")
release = importlib.util.module_from_spec(_implementation_spec)
sys.modules[_implementation_name] = release
_implementation_spec.loader.exec_module(release)


VERSION = "0.16.0"

# Reuse the audited archive and verification implementation while keeping the
# 0.15.6 release entry point and its filenames immutable.
release.VERSION = VERSION
release.__doc__ = "Build, inspect, verify, and assemble Sona 0.16.0 platform artifacts."
release.NATIVE_SPECS = {
    ("windows", "x86_64"): release._spec("windows", "x86_64", "x86_64-pc-windows-msvc", "x86_64"),
    ("linux", "x86_64"): release._spec("linux", "x86_64", "x86_64-unknown-linux-musl", "x86_64-musl"),
    ("linux", "aarch64"): release._spec("linux", "aarch64", "aarch64-unknown-linux-musl", "aarch64-musl"),
    ("macos", "x86_64"): release._spec("macos", "x86_64", "x86_64-apple-darwin", "x86_64"),
    ("macos", "aarch64"): release._spec("macos", "aarch64", "aarch64-apple-darwin", "aarch64"),
}
release.WHEEL_NAME = f"sona_lang-{VERSION}-py3-none-any.whl"
release.SDIST_NAME = f"sona_lang-{VERSION}.tar.gz"
release.VSIX_NAME = f"sona-ai-native-programming-{VERSION}.vsix"
release.TEST_KIT_NAME = f"sona-{VERSION}-platform-test-kit.zip"
release.PORTABLE_REPORT_NAME = f"sona-{VERSION}-portable-report.json"
release.RELEASE_MANIFEST_NAME = f"sona-{VERSION}-release-manifest.json"
release.PORTABLE_ASSETS = {
    release.WHEEL_NAME,
    release.SDIST_NAME,
    release.VSIX_NAME,
    release.TEST_KIT_NAME,
}
release.NATIVE_ASSETS = {item.archive_name for item in release.NATIVE_SPECS.values()}
release.RELEASE_ASSETS = release.PORTABLE_ASSETS | release.NATIVE_ASSETS

NATIVE_ASSETS = release.NATIVE_ASSETS
WHEEL_NAME = release.WHEEL_NAME
SDIST_NAME = release.SDIST_NAME
VSIX_NAME = release.VSIX_NAME
TEST_KIT_NAME = release.TEST_KIT_NAME
PORTABLE_ASSETS = release.PORTABLE_ASSETS
RELEASE_ASSETS = release.RELEASE_ASSETS


if __name__ == "__main__":
    raise SystemExit(release.main())
