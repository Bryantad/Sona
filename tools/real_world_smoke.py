#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE_PROGRAM = ROOT / "tools" / "smoke" / "real_world_smoke.sona"


def _exe_in_venv(venv_dir: Path, name: str) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / name
    return venv_dir / "bin" / name


def _run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        env=run_env,
    )
    if proc.returncode != 0:
        print("[smoke] command failed:")
        print("  ", " ".join(cmd))
        if proc.stdout:
            print("[smoke] stdout:\n" + proc.stdout)
        if proc.stderr:
            print("[smoke] stderr:\n" + proc.stderr)
        raise SystemExit(proc.returncode)
    return proc


def _validate_receipt(receipt_path: Path) -> None:
    if not receipt_path.exists():
        raise SystemExit(f"[smoke] receipt not found: {receipt_path}")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"[smoke] receipt invalid JSON: {exc}")

    required_top = {
        "sona_version",
        "receipt_version",
        "timestamp_utc",
        "code",
        "dependencies",
        "inputs",
        "execution",
        "reproduce",
    }
    missing = sorted(required_top.difference(receipt.keys()))
    if missing:
        raise SystemExit(f"[smoke] receipt missing keys: {missing}")

    if not isinstance(receipt.get("execution"), dict):
        raise SystemExit("[smoke] receipt.execution must be an object")


def _create_venv(venv_dir: Path) -> Path:
    builder = venv.EnvBuilder(with_pip=True, clear=True)
    builder.create(str(venv_dir))
    py = _exe_in_venv(venv_dir, "python.exe" if os.name == "nt" else "python")
    if not py.exists():
        raise SystemExit(f"[smoke] python not found in venv: {py}")
    return py


def main() -> int:
    parser = argparse.ArgumentParser(description="Real-world Sona smoke test (CLI subprocess, optional fresh venv install)")
    parser.add_argument(
        "--fresh-venv",
        action="store_true",
        help="Create a temporary venv and install the package before running smoke",
    )
    parser.add_argument(
        "--venv-dir",
        default=None,
        help="Optional venv directory (defaults to a temp dir when --fresh-venv is set)",
    )
    args = parser.parse_args()

    if not SMOKE_PROGRAM.exists():
        print(f"[smoke] missing smoke program: {SMOKE_PROGRAM}")
        return 1

    with tempfile.TemporaryDirectory(prefix="sona_real_world_smoke_") as tmp:
        tmp_path = Path(tmp)
        work_dir = tmp_path / "work"
        work_dir.mkdir(parents=True, exist_ok=True)

        program_path = work_dir / "real_world_smoke.sona"
        program_path.write_text(SMOKE_PROGRAM.read_text(encoding="utf-8"), encoding="utf-8")

        receipt_path = work_dir / "receipt.json"

        if args.fresh_venv:
            venv_dir = Path(args.venv_dir) if args.venv_dir else (tmp_path / "venv")
            py = _create_venv(venv_dir)
            _run([str(py), "-m", "pip", "install", "-U", "pip"], cwd=ROOT)

            # Install the package so the console script/entrypoint works.
            _run([str(py), "-m", "pip", "install", "-e", str(ROOT)], cwd=ROOT)

            sona_exe = _exe_in_venv(venv_dir, "sona.exe" if os.name == "nt" else "sona")
            if sona_exe.exists():
                sona_cmd = [str(sona_exe)]
            else:
                # Fallback: still run the real CLI code path, even if scripts aren't created.
                sona_cmd = [str(py), "-m", "sona.cli"]

            # Optional: prove the installed CLI can answer version.
            _run(sona_cmd + ["version"], cwd=work_dir)

            # Real CLI subprocess run with receipt
            _run(sona_cmd + ["run", str(program_path), "--receipt", str(receipt_path)], cwd=work_dir)

            # Also smoke the repo runner (common real-world usage in this repo)
            _run([str(py), str(ROOT / "run_sona.py"), "run", str(program_path)], cwd=ROOT)

        else:
            # Use current interpreter, but still run CLI via subprocess (no in-process calls).
            sona_cmd = [sys.executable, "-m", "sona.cli"]
            existing_pythonpath = os.environ.get("PYTHONPATH", "")
            if existing_pythonpath:
                pythonpath = str(ROOT) + os.pathsep + existing_pythonpath
            else:
                pythonpath = str(ROOT)
            run_env = {"PYTHONPATH": pythonpath}

            _run(
                sona_cmd + ["run", str(program_path), "--receipt", str(receipt_path)],
                cwd=work_dir,
                env=run_env,
            )
            _run([sys.executable, str(ROOT / "run_sona.py"), "run", str(program_path)], cwd=ROOT)

        _validate_receipt(receipt_path)
        print("[smoke] OK")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
