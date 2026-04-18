#!/usr/bin/env python3
"""Build a deterministic VSIX for the Sona Receipt Explorer extension.

This script packages the extension with `vsce`, then rewrites the archive with:
- fixed timestamp metadata
- stable file ordering
- fixed file mode bits
- no compression (ZIP_STORED) for byte-stable output across environments
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

CANONICAL_ZIP_TIMESTAMP = (2020, 1, 1, 0, 0, 0)
CANONICAL_FILE_MODE = 0o100644 << 16
CANONICAL_DIR_MODE = (0o40755 << 16) | 0x10


def run(cmd: list[str], cwd: Path) -> None:
    if os.name == "nt" and cmd and cmd[0] in {"npm", "npx"}:
        cmd = [f"{cmd[0]}.cmd", *cmd[1:]]
    subprocess.run(cmd, cwd=str(cwd), check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonicalize_vsix(source: Path, output: Path) -> None:
    entries: list[tuple[str, bool, bytes]] = []
    with zipfile.ZipFile(source, "r") as zin:
        for info in zin.infolist():
            name = info.filename
            is_dir = name.endswith("/")
            data = b"" if is_dir else zin.read(name)
            entries.append((name, is_dir, data))

    entries.sort(key=lambda item: item[0])

    tmp_output = output.with_suffix(output.suffix + ".tmp")
    if tmp_output.exists():
        tmp_output.unlink()

    with zipfile.ZipFile(tmp_output, "w", compression=zipfile.ZIP_STORED) as zout:
        for name, is_dir, data in entries:
            zip_info = zipfile.ZipInfo(name, date_time=CANONICAL_ZIP_TIMESTAMP)
            zip_info.create_system = 3  # Unix
            zip_info.flag_bits = 0x800  # UTF-8 names
            zip_info.external_attr = CANONICAL_DIR_MODE if is_dir else CANONICAL_FILE_MODE
            zip_info.compress_type = zipfile.ZIP_STORED
            zout.writestr(zip_info, b"" if is_dir else data)

    tmp_output.replace(output)


def package_once(root: Path, raw_vsix: Path, final_vsix: Path) -> str:
    run(["npm", "run", "compile"], cwd=root)
    run(
        [
            "npx",
            "@vscode/vsce",
            "package",
            "--out",
            str(raw_vsix),
        ],
        cwd=root,
    )
    canonicalize_vsix(raw_vsix, final_vsix)
    return sha256(final_vsix)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Build twice and verify deterministic output hashes are identical.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    package_json = root / "package.json"
    package_data = json.loads(package_json.read_text(encoding="utf-8"))
    name = package_data["name"]
    version = package_data["version"]

    build_dir = root / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    raw_a = build_dir / f"{name}-{version}-raw-a.vsix"
    out_a = root / f"{name}-{version}.vsix"

    for path in (raw_a, out_a):
        if path.exists():
            path.unlink()

    hash_a = package_once(root, raw_a, out_a)
    print(f"deterministic-vsix: {out_a.name}")
    print(f"sha256: {hash_a}")

    if not args.verify:
        return 0

    raw_b = build_dir / f"{name}-{version}-raw-b.vsix"
    out_b = build_dir / f"{name}-{version}-verify.vsix"
    for path in (raw_b, out_b):
        if path.exists():
            path.unlink()

    hash_b = package_once(root, raw_b, out_b)
    print(f"verify-sha256: {hash_b}")

    if hash_a != hash_b:
        print("ERROR: deterministic build verification failed (hash mismatch).", file=sys.stderr)
        return 1

    print("deterministic build verification passed (hashes match).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
