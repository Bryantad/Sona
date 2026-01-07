import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    sys.stdout.write(proc.stdout)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def _spm_cmd() -> list[str]:
    """Prefer the console script if present; otherwise use module invocation."""
    exe = shutil.which("spm")
    if exe:
        return [exe]
    return [sys.executable, "-m", "sona_spm.spm"]


def main() -> int:
    spm = _spm_cmd()

    # 1) Help should work
    _run(spm + ["--help"])

    # 2) Init should create a manifest in an empty folder
    with tempfile.TemporaryDirectory(prefix="spm_smoke_") as tmp:
        root = Path(tmp)
        _run(spm + ["--root", str(root), "init", "--name", "spm-smoke", "--version", "0.0.0"])

        manifest_path = root / "sona.json"
        if not manifest_path.exists():
            raise SystemExit("smoke_test failed: sona.json not created")

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise SystemExit(f"smoke_test failed: invalid JSON in sona.json: {exc}")

        if manifest.get("name") != "spm-smoke":
            raise SystemExit("smoke_test failed: manifest name mismatch")

    print("SPM smoke test: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
