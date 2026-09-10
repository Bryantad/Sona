#!/usr/bin/env python3
"""Run manifest examples, without modifying the source examples tree."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def run_examples(*, verbose: bool = False, include_native: bool = False) -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from sona.example_catalog import ExampleError, load_manifest
    from sona.example_runner import run_example
    from sona.native_launcher import NativeProofLaunchError

    entries = load_manifest()["examples"]
    selected = [entry for entry in entries if include_native or entry["runtime"] == "python"]
    print(f"Running {len(selected)} manifest examples...")
    for entry in selected:
        try:
            result = run_example(entry["name"])
        except (ExampleError, NativeProofLaunchError) as exc:
            print(f"{exc.diagnostic_id}: {exc.message}", file=sys.stderr)
            return 1
        if verbose and result["execution"]["stdout"]:
            print(result["execution"]["stdout"].rstrip())
        print(f"{result['status'].upper()} {entry['name']}")
        if result["status"] != "passed":
            print(result, file=sys.stderr)
            return 1
    if not include_native:
        print("Native examples NOT RUN; use --include-native with matching Native Core installed.")
    print("All selected examples passed.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--include-native", action="store_true")
    args = parser.parse_args(argv)
    return run_examples(verbose=args.verbose, include_native=args.include_native)


if __name__ == "__main__":
    raise SystemExit(main())
