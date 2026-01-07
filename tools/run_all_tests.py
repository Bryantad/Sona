#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
import json
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import run_sona


TEST_PLAN = [
    ("Running complete verification test", "test_all_096.sona"),
    ("Running basic modules test", "test_stdlib_basics.sona"),
    ("Running data processing test", "test_stdlib_data.sona"),
    ("Running collections test", "test_stdlib_collections.sona"),
    ("Running time and random test", "test_stdlib_time.sona"),
    ("Running filesystem test", "test_stdlib_filesystem.sona"),
    ("Running regex test", "test_stdlib_regex.sona"),
    ("Running smod imports test", "test_smod_imports_010.sona"),
    ("Running cognitive focus test", "test_cognitive_focus_010.sona"),
    ("Running simple arithmetic test", "test.sona"),
]


def _run_receipt_smoke(root: Path) -> int:
    """Basic verification that `--receipt` produces a JSON receipt with expected keys."""
    with tempfile.TemporaryDirectory(prefix="sona_receipt_") as tmp:
        receipt_path = Path(tmp) / "receipt.json"
        target = root / "test.sona"
        if not target.exists():
            print("ERROR: receipt smoke test requires test.sona")
            return 1

        exit_code = run_sona.main(["run", str(target), "--receipt", str(receipt_path)])
        if exit_code != 0:
            print("ERROR: receipt smoke test failed to run program")
            return 1
        if not receipt_path.exists():
            print("ERROR: receipt smoke test did not create receipt.json")
            return 1

        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"ERROR: receipt smoke test produced invalid JSON: {exc}")
            return 1

        required_top = {"sona_version", "receipt_version", "timestamp_utc", "code", "dependencies", "inputs", "execution", "reproduce"}
        missing = sorted(required_top.difference(receipt.keys()))
        if missing:
            print(f"ERROR: receipt missing keys: {missing}")
            return 1

        if not isinstance(receipt.get("code"), dict):
            print("ERROR: receipt.code must be an object")
            return 1
        if not isinstance(receipt.get("execution"), dict):
            print("ERROR: receipt.execution must be an object")
            return 1
        if not isinstance(receipt["execution"].get("exit_code"), int):
            print("ERROR: receipt.execution.exit_code must be int")
            return 1
        if not isinstance(receipt["execution"].get("duration_ms"), int):
            print("ERROR: receipt.execution.duration_ms must be int")
            return 1

        return 0


def run_suite() -> int:
    total = len(TEST_PLAN)
    print("========================================")
    print("Sona 0.10.1 - Test Suite Runner")
    print("========================================")
    print("")

    for index, (label, filename) in enumerate(TEST_PLAN, start=1):
        print(f"[{index}/{total}] {label}...")
        path = ROOT / filename
        if not path.exists():
            print(f"ERROR: {filename} not found!")
            return 1
        exit_code, _source, _error = run_sona.run_sona_file(str(path))
        if exit_code != 0:
            print(f"ERROR: {filename} failed!")
            return 1
        print("")

    print("[receipt] Running receipt smoke test...")
    if _run_receipt_smoke(ROOT) != 0:
        return 1
    print("")

    print("========================================")
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("========================================")
    print("")
    print("Sona 0.10.1 is fully operational.")
    print("")
    return 0


def main() -> int:
    return run_suite()


if __name__ == "__main__":
    raise SystemExit(main())
