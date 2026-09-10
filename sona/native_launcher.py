"""Bounded Native Core version preflight for the Python Proof Mode coordinator."""

from __future__ import annotations

import contextlib
import os
import re
import subprocess
import threading
from pathlib import Path

PROBE_TIMEOUT_SECONDS = 5.0
PROBE_MAX_BYTES = 4096
_VERSION_LINE = re.compile(
    rb"Sona native ([0-9]{1,9}\.[0-9]{1,9}\.[0-9]{1,9}"
    rb"(?:-[0-9A-Za-z.-]{1,64})?(?:\+[0-9A-Za-z.-]{1,64})?)(?:\r?\n)?"
)


class NativeProofLaunchError(Exception):
    """A redacted failure before the Native Proof Mode producer starts."""

    def __init__(
        self, message: str, hint: str, diagnostic_id: str = "SONA-NATIVE-LAUNCH-001"
    ):
        super().__init__(message)
        self.message = message
        self.hint = hint
        self.diagnostic_id = diagnostic_id

    def to_dict(self) -> dict[str, str]:
        return {
            "diagnostic_id": self.diagnostic_id,
            "category": "native-launch",
            "severity": "error",
            "message": self.message,
            "hint": self.hint,
        }


def _probe_output(arguments: list[str], environment: dict[str, str]) -> tuple[int, bytes]:
    """Read at most one bounded version response; never inherit program stdin."""

    try:
        process = subprocess.Popen(
            arguments,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
    except (OSError, ValueError) as exc:
        raise NativeProofLaunchError(
            "Native Core could not be started safely.",
            "Check the sona-native installation or SONA_NATIVE_BINARY configuration.",
        ) from exc

    output = bytearray()
    read_failed = threading.Event()

    def read_output() -> None:
        assert process.stdout is not None
        try:
            with process.stdout:
                while len(output) <= PROBE_MAX_BYTES:
                    chunk = process.stdout.read1(PROBE_MAX_BYTES + 1 - len(output))
                    if not chunk:
                        return
                    output.extend(chunk)
                with contextlib.suppress(OSError):
                    process.kill()
        except OSError:
            read_failed.set()

    reader = threading.Thread(target=read_output, name="sona-native-version", daemon=True)
    reader.start()
    try:
        returncode = process.wait(timeout=PROBE_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        raise NativeProofLaunchError(
            "Native Core did not report its version in time.",
            "Check the selected Native Core installation before retrying Proof Mode.",
            "SONA-NATIVE-LAUNCH-004",
        ) from exc
    finally:
        if process.poll() is None:
            with contextlib.suppress(OSError):
                process.kill()
            process.wait(timeout=1)
        reader.join(timeout=1)

    if reader.is_alive() or read_failed.is_set() or len(output) > PROBE_MAX_BYTES:
        raise NativeProofLaunchError(
            "Native Core returned an invalid version response.",
            "Select the standalone Native Core executable with SONA_NATIVE_BINARY.",
            "SONA-NATIVE-LAUNCH-002",
        )
    return returncode, bytes(output)


def probe_native_version(
    binary: Path, expected_version: str, environment: dict[str, str]
) -> str:
    """Require an exact version match; this is compatibility, not authentication."""

    source = "SONA_NATIVE_BINARY" if "SONA_NATIVE_BINARY" in environment else "PATH (sona-native)"
    # Windows can execute batch files through a command shell even with shell=False.
    if os.name == "nt" and binary.suffix.lower() in {".bat", ".cmd"}:
        raise NativeProofLaunchError(
            "Native Core must be a standalone executable, not a batch wrapper.",
            f"Check {source} and select the extracted Native Core executable.",
            "SONA-NATIVE-LAUNCH-002",
        )
    try:
        returncode, output = _probe_output([str(binary), "--version"], environment)
    except NativeProofLaunchError as exc:
        raise NativeProofLaunchError(
            exc.message, f"Selected by {source}. {exc.hint}", exc.diagnostic_id
        ) from exc

    match = _VERSION_LINE.fullmatch(output)
    if returncode != 0 or match is None:
        raise NativeProofLaunchError(
            "Native Core returned an invalid version response.",
            f"Check {source}; the executable must report 'Sona native <version>'.",
            "SONA-NATIVE-LAUNCH-002",
        )
    version = match[1].decode("ascii")
    if version != expected_version:
        raise NativeProofLaunchError(
            f"Sona CLI {expected_version} and Native Core {version} do not match.",
            f"Selected by {source}. Install Native Core {expected_version} and update "
            "that selection before retrying. No program was executed.",
            "SONA-NATIVE-LAUNCH-003",
        )
    return version
