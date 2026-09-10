from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from sona import cli
from sona.proof import verify_receipt

ROOT = Path(__file__).resolve().parents[2]


def test_generation_routing_reserves_python_receipt_actions_and_help():
    assert cli._proof_generation_arguments(["sona", "proof", "verify", "proof.json"]) is None
    assert cli._proof_generation_arguments(["sona", "proof", "inspect", "proof.json"]) is None
    assert cli._proof_generation_arguments(["sona", "proof", "--help"]) is None
    assert cli._proof_generation_arguments(["sona", "proof"]) is None
    assert cli._proof_generation_arguments(["sona", "run", "app.sona"]) is None

    assert cli._proof_generation_arguments(
        ["sona", "proof", "app.sona", "--receipt", "app.sproof", "--allow-fs-read"]
    ) == ["app.sona", "--receipt", "app.sproof", "--allow-fs-read"]


def test_explicit_native_binary_has_priority_over_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    configured = tmp_path / "configured-native"
    configured.write_bytes(b"native-placeholder")

    def unexpected_lookup(*_args, **_kwargs):
        raise AssertionError("PATH discovery must not run when SONA_NATIVE_BINARY is set")

    monkeypatch.setattr(cli.shutil, "which", unexpected_lookup)

    resolved = cli._resolve_native_proof_binary(
        {"SONA_NATIVE_BINARY": str(configured), "PATH": "ignored"}
    )

    assert resolved == configured.resolve()


def test_path_discovery_uses_only_sona_native(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    native = tmp_path / "sona-native"
    native.write_bytes(b"native-placeholder")
    calls: list[tuple[str, str | None]] = []

    def lookup(name: str, *, path: str | None = None) -> str:
        calls.append((name, path))
        return str(native)

    monkeypatch.setattr(cli.shutil, "which", lookup)

    resolved = cli._resolve_native_proof_binary({"PATH": "native-search-path"})

    assert resolved == native.resolve()
    assert calls == [("sona-native", "native-search-path")]


def test_invalid_explicit_native_binary_fails_without_path_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    calls: list[str] = []
    monkeypatch.setattr(cli.shutil, "which", lambda name, **_kwargs: calls.append(name))

    with pytest.raises(cli.NativeProofLaunchError) as raised:
        cli._resolve_native_proof_binary(
            {"SONA_NATIVE_BINARY": str(tmp_path / "missing-native"), "PATH": "ignored"}
        )

    assert "unavailable" in raised.value.message.lower()
    assert calls == []


def test_native_delegation_forwards_arguments_without_a_shell_and_preserves_exit_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    native = tmp_path / "sona-native"
    native.write_bytes(b"native-placeholder")
    observed: dict[str, object] = {}

    monkeypatch.setattr(cli, "_resolve_native_proof_binary", lambda _environment: native)

    def probe(binary, expected_version, environment):
        assert binary == native
        assert expected_version == cli.SONA_VERSION
        assert environment["PATH"] == "native-search-path"
        observed["probed"] = True
        return expected_version

    monkeypatch.setattr(cli, "probe_native_version", probe)

    def run(arguments, **kwargs):
        assert observed["probed"] is True
        observed["arguments"] = arguments
        observed["kwargs"] = kwargs
        return subprocess.CompletedProcess(arguments, 7)

    monkeypatch.setattr(cli.subprocess, "run", run)
    arguments = ["app.sona", "--receipt", "app.sproof", "--guardian-root", "."]

    result = cli._delegate_native_proof(arguments, {"PATH": "native-search-path"})

    assert result == 7
    assert observed["arguments"] == [str(native), "proof", *arguments]
    kwargs = observed["kwargs"]
    assert isinstance(kwargs, dict)
    assert kwargs["shell"] is False
    assert kwargs["check"] is False
    assert "stdout" not in kwargs
    assert "stderr" not in kwargs
    assert "capture_output" not in kwargs
    assert kwargs["env"]["_SONA_NATIVE_PROOF_DELEGATED"] == "1"


def test_native_delegation_guard_prevents_python_launcher_recursion(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    monkeypatch.setattr(
        cli.subprocess,
        "run",
        lambda *_args, **_kwargs: pytest.fail("recursion guard must stop before launch"),
    )

    result = cli._delegate_native_proof(
        ["app.sona", "--receipt", "app.sproof"],
        {"_SONA_NATIVE_PROOF_DELEGATED": "1"},
    )

    assert result == 1
    assert "returned to the Python CLI" in capsys.readouterr().err


def test_native_launch_os_error_is_redacted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    native = tmp_path / "sona-native"
    native.write_bytes(b"native-placeholder")
    monkeypatch.setattr(cli, "_resolve_native_proof_binary", lambda _environment: native)
    monkeypatch.setattr(cli, "probe_native_version", lambda _binary, version, _env: version)
    monkeypatch.setattr(
        cli.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            OSError("private operating-system launch detail")
        ),
    )

    result = cli._delegate_native_proof(["app.sona", "--receipt", "app.sproof"], {})

    error = capsys.readouterr().err
    assert result == 1
    assert "Native Core could not be started safely" in error
    assert "private operating-system launch detail" not in error


def test_main_routes_proof_generation_before_argparse(monkeypatch: pytest.MonkeyPatch):
    arguments = ["app.sona", "--receipt", "app.sproof", "--engine", "native"]
    observed: list[list[str]] = []
    monkeypatch.setattr(cli.sys, "argv", ["sona", "proof", *arguments])
    monkeypatch.setattr(
        cli,
        "_delegate_native_proof",
        lambda forwarded: observed.append(forwarded) or 9,
    )

    assert cli.main() == 9
    assert observed == [arguments]


def test_missing_native_core_fails_closed_with_install_hint(tmp_path: Path):
    source = tmp_path / "app.sona"
    source.write_text('print("not executed");\n', encoding="utf-8")
    receipt = tmp_path / "app.sproof"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    environment["PATH"] = ""
    environment.pop("SONA_NATIVE_BINARY", None)

    process = subprocess.run(
        [sys.executable, "-m", "sona", "proof", str(source), "--receipt", str(receipt)],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        shell=False,
    )

    assert process.returncode == 1
    assert process.stdout == ""
    assert "Native Core is required" in process.stderr
    assert "SONA_NATIVE_BINARY" in process.stderr
    assert not receipt.exists()


def test_python_cli_delegates_real_native_proof_and_shared_verifier_accepts_it(
    tmp_path: Path,
    native_binary: Path,
):
    source = tmp_path / "delegated.sona"
    source.write_text('print("delegated proof");\n', encoding="utf-8")
    receipt = tmp_path / "delegated.sproof"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    environment["SONA_NATIVE_BINARY"] = str(native_binary)

    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "sona",
            "proof",
            str(source),
            "--receipt",
            str(receipt),
            "--engine",
            "native",
        ],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        shell=False,
        timeout=30,
    )

    assert process.returncode == 0, process.stderr or process.stdout
    assert process.stdout == "delegated proof\n"
    assert process.stderr == ""
    result = verify_receipt(receipt)
    assert result["status"] == "valid"
    assert result["engine"]["name"] == "native"
    assert result["engine"]["python_required"] is False
    assert result["engine"]["python_embedded"] is False
    assert result["engine"]["fallback_used"] is False


def test_python_proof_help_describes_generation_without_native_discovery():
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    environment.pop("SONA_NATIVE_BINARY", None)

    process = subprocess.run(
        [sys.executable, "-m", "sona", "proof", "--help"],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        shell=False,
    )

    assert process.returncode == 0, process.stderr or process.stdout
    assert "Generate a receipt with Native Core" in process.stdout
    assert "sona proof <program.sona|program.sbc>" in process.stdout
    assert "{verify,inspect}" in process.stdout
