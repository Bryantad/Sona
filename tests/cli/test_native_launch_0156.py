from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from sona import cli, native_launcher
from sona.native_launcher import NativeProofLaunchError, probe_native_version


@pytest.mark.parametrize("version", ["0.15.4", "0.15.7", "0.15.5-rc.1", "0.15.5+other"])
@pytest.mark.parametrize("selection", ["PATH", "SONA_NATIVE_BINARY"])
def test_mismatch_never_starts_proof(tmp_path, monkeypatch, capsys, version, selection):
    native = tmp_path / "sona-native.exe"
    native.touch()
    environment = {selection: str(native)}
    monkeypatch.setattr(cli, "_resolve_native_proof_binary", lambda _: native)
    monkeypatch.setattr(
        native_launcher, "_probe_output",
        lambda _args, _env: (0, f"Sona native {version}\n".encode()),
    )
    monkeypatch.setattr(
        cli.subprocess, "run", lambda *_a, **_k: pytest.fail("must not execute program")
    )
    assert cli._delegate_native_proof(["app.sona", "--receipt", "app.sproof"], environment) == 1
    error = capsys.readouterr().err
    assert "SONA-NATIVE-LAUNCH-003" in error
    assert f"Sona CLI {cli.SONA_VERSION} and Native Core {version}" in error
    assert selection in error
    assert str(tmp_path) not in error


@pytest.mark.parametrize("output,code", [
    (b"", 0),
    (b"Sona 0.15.6\n", 0),
    (b"Sona native 0.15.6\nprivate error detail", 0),
    (b"Sona native 0.15.6\n", 3),
    (b"Sona native \xff\n", 0),
    (b"Sona native 0.15.6\n\n", 0),
    (b"Sona native 0.15\n", 0),
    (b"Sona native 0.15.6\x1b[2J", 0),
])
def test_invalid_probe_fails_without_echoing_output(monkeypatch, output, code):
    monkeypatch.setattr(native_launcher, "_probe_output", lambda *_: (code, output))
    with pytest.raises(NativeProofLaunchError) as caught:
        probe_native_version(Path("sona-native.exe"), cli.SONA_VERSION, {})
    assert caught.value.diagnostic_id == "SONA-NATIVE-LAUNCH-002"
    assert "private error detail" not in str(caught.value)
    assert "\x1b" not in str(caught.value)


@pytest.mark.parametrize("suffix", [b"", b"\n", b"\r\n"])
def test_exact_version_accepts_native_line_endings(monkeypatch, suffix):
    seen = []

    def probe(arguments, environment):
        seen.append((arguments, environment))
        return 0, f"Sona native {cli.SONA_VERSION}".encode() + suffix

    monkeypatch.setattr(native_launcher, "_probe_output", probe)
    binary = Path("folder with spaces") / "sona-native.exe"
    assert probe_native_version(binary, cli.SONA_VERSION, {"PATH": "test"}) == cli.SONA_VERSION
    assert seen == [([str(binary), "--version"], {"PATH": "test"})]


def test_real_probe_uses_no_stdin_and_discards_stderr():
    returncode, output = native_launcher._probe_output(
        [sys.executable, "-c",
         "import sys; assert sys.stdin.read() == ''; "
         "sys.stderr.write('private diagnostic'); print('Sona native 0.15.6')"],
        os.environ.copy(),
    )
    assert returncode == 0
    assert output == b"Sona native 0.15.6\r\n" if os.name == "nt" else output == b"Sona native 0.15.6\n"


def test_real_probe_timeout_is_redacted_and_child_is_reaped(monkeypatch):
    processes = []
    popen = subprocess.Popen

    def start(*args, **kwargs):
        process = popen(*args, **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(native_launcher.subprocess, "Popen", start)
    monkeypatch.setattr(native_launcher, "PROBE_TIMEOUT_SECONDS", 0.25)
    with pytest.raises(NativeProofLaunchError) as caught:
        native_launcher._probe_output(
            [sys.executable, "-c", "import time; time.sleep(30)"], os.environ.copy()
        )
    assert caught.value.diagnostic_id == "SONA-NATIVE-LAUNCH-004"
    assert processes[0].poll() is not None


def test_real_probe_output_is_bounded_and_child_is_reaped(monkeypatch):
    processes = []
    popen = subprocess.Popen

    def start(*args, **kwargs):
        process = popen(*args, **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(native_launcher.subprocess, "Popen", start)
    with pytest.raises(NativeProofLaunchError) as caught:
        native_launcher._probe_output(
            [sys.executable, "-c", "import sys; sys.stdout.write('x' * 1000000)"],
            os.environ.copy(),
        )
    assert caught.value.diagnostic_id == "SONA-NATIVE-LAUNCH-002"
    assert processes[0].poll() is not None


def test_missing_executable_does_not_leak_host_path(tmp_path):
    with pytest.raises(NativeProofLaunchError) as caught:
        probe_native_version(tmp_path / "private-missing.exe", cli.SONA_VERSION, {})
    assert caught.value.diagnostic_id == "SONA-NATIVE-LAUNCH-001"
    assert str(tmp_path) not in str(caught.value)
    assert "private-missing" not in str(caught.value)


def test_python_launcher_hardlink_is_rejected(tmp_path, monkeypatch):
    launcher = tmp_path / "sona.exe"
    launcher.touch()
    alias = tmp_path / "sona-native.exe"
    alias.hardlink_to(launcher)
    monkeypatch.setattr(cli.sys, "argv", [str(launcher)])
    with pytest.raises(NativeProofLaunchError, match="Python Sona launcher"):
        cli._resolve_native_proof_binary({"SONA_NATIVE_BINARY": str(alias)})


@pytest.mark.parametrize("configured", ["", "\x00", "missing-native.exe"])
def test_malformed_explicit_selection_never_uses_path(configured, monkeypatch):
    monkeypatch.setattr(cli.shutil, "which", lambda *_a, **_k: pytest.fail("no fallback"))
    with pytest.raises(NativeProofLaunchError):
        cli._resolve_native_proof_binary({"SONA_NATIVE_BINARY": configured})


@pytest.mark.skipif(os.name != "nt", reason="Windows batch shell behavior")
@pytest.mark.parametrize("suffix", [".cmd", ".bat", ".CMD"])
def test_windows_batch_wrappers_are_rejected_without_execution(suffix, monkeypatch):
    monkeypatch.setattr(
        native_launcher, "_probe_output", lambda *_: pytest.fail("must not start batch")
    )
    with pytest.raises(NativeProofLaunchError, match="batch wrapper"):
        probe_native_version(Path("sona-native" + suffix), cli.SONA_VERSION, {})


def test_real_native_version_is_checked(native_binary):
    assert probe_native_version(native_binary, cli.SONA_VERSION, os.environ.copy()) == cli.SONA_VERSION


def test_receipt_verification_does_not_probe_native(monkeypatch, capsys):
    fixture = Path(__file__).parents[1] / "proof" / "fixtures" / "0.15.4-native-hello.json"
    monkeypatch.setattr(cli.sys, "argv", ["sona", "proof", "verify", str(fixture)])
    monkeypatch.setattr(cli, "probe_native_version", lambda *_: pytest.fail("read-only verify"))
    assert cli.main() == 0
    assert "VALID" in capsys.readouterr().out
