import os
import sys
from pathlib import Path

from sona import cli
from sona.lockfile_manager import generate_lockfile, verify_lockfile


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run_cli(args, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["sona"] + args)
    return cli.main()


def test_generate_and_verify_lockfile(tmp_path):
    _write(tmp_path / "sona" / "runtime.py", "print('runtime')\n")
    _write(tmp_path / "stdlib" / "math.smod", "export func add(a, b) { return a + b; }\n")
    _write(tmp_path / "pyproject.toml", "[project]\nname = 'sona'\n")

    assert generate_lockfile(tmp_path) is True
    assert (tmp_path / "sona.lock.json").exists()
    assert verify_lockfile(tmp_path) is True


def test_verify_lockfile_detects_mutation(tmp_path):
    _write(tmp_path / "sona" / "runtime.py", "print('runtime')\n")
    _write(tmp_path / "stdlib" / "math.smod", "export func add(a, b) { return a + b; }\n")

    assert generate_lockfile(tmp_path) is True
    assert verify_lockfile(tmp_path) is True

    _write(tmp_path / "sona" / "runtime.py", "print('changed runtime')\n")
    assert verify_lockfile(tmp_path) is False


def test_cli_lock_and_verify(tmp_path, monkeypatch):
    _write(tmp_path / "sona" / "runtime.py", "print('runtime')\n")
    _write(tmp_path / "stdlib" / "math.smod", "export func add(a, b) { return a + b; }\n")

    previous_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        assert _run_cli(["lock"], monkeypatch) == 0
        assert (tmp_path / "sona.lock.json").exists()
        assert _run_cli(["verify"], monkeypatch) == 0
    finally:
        os.chdir(previous_cwd)
