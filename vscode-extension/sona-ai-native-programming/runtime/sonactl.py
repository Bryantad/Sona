#!/usr/bin/env python3
import argparse
import importlib
import os
import sys
import traceback


def _runtime_root():
    return os.path.dirname(os.path.abspath(__file__))


def _ensure_runtime_on_path():
    root = _runtime_root()
    if root not in sys.path:
        sys.path.insert(0, root)


def _verify():
    _ensure_runtime_on_path()
    try:
        import sona  # noqa: F401
        for name in ("json", "string", "math"):
            importlib.import_module(f"sona.stdlib.{name}")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1
    print("OK: core stdlib imported")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        return _verify()
    print("Sona runtime staged. Install full Sona for REPL.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
