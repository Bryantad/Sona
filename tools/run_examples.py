#!/usr/bin/env python3
"""Run the official Sona 0.15.1 examples in an isolated temp workspace."""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import shutil
import sys
import tempfile
import gc
from pathlib import Path


OFFICIAL_EXAMPLES = [
    "hello.sona",
    "variables_math.sona",
    "functions.sona",
    "control_flow.sona",
    "stdlib_math.sona",
    "stdlib_string.sona",
    "stdlib_json.sona",
    "stdlib_fs.sona",
    "calculator.sona",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _clean_runtime_artifacts(root: Path) -> None:
    for path in root.rglob(".sona"):
        if path.is_dir() and root in path.resolve().parents:
            shutil.rmtree(path, ignore_errors=True)


def _copy_examples(src_dir: Path, dst_dir: Path) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)
    for name in OFFICIAL_EXAMPLES:
        src = src_dir / name
        if not src.exists():
            raise FileNotFoundError(f"missing official example: {src}")
        shutil.copy2(src, dst_dir / name)


def run_examples(*, verbose: bool = False) -> int:
    root = _repo_root()
    examples_dir = root / "examples"
    _clean_runtime_artifacts(examples_dir)

    sys.path.insert(0, str(root))
    import run_sona  # noqa: PLC0415
    from sona.interpreter import SonaUnifiedInterpreter  # noqa: PLC0415

    with tempfile.TemporaryDirectory(prefix="sona_examples_", ignore_cleanup_errors=True) as tmp:
        tmp_root = Path(tmp)
        tmp_examples = tmp_root / "examples"
        _copy_examples(examples_dir, tmp_examples)
        _clean_runtime_artifacts(tmp_root)

        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_root)
            print(f"Running {len(OFFICIAL_EXAMPLES)} examples...")
            for name in OFFICIAL_EXAMPLES:
                rel_path = Path("examples") / name
                if verbose:
                    print(f"[examples] running {rel_path}")
                interpreter = SonaUnifiedInterpreter(project_root=tmp_root)
                stdout = io.StringIO()
                stderr = io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    code, _source, _error = run_sona.run_sona_file(
                        str(rel_path),
                        interpreter=interpreter,
                    )
                del interpreter
                gc.collect()
                if code != 0:
                    print(f"[examples] failed: {name}", file=sys.stderr)
                    if stdout.getvalue():
                        print(stdout.getvalue().rstrip(), file=sys.stderr)
                    if stderr.getvalue():
                        print(stderr.getvalue().rstrip(), file=sys.stderr)
                    return code or 1
                if verbose and stdout.getvalue():
                    print(stdout.getvalue().rstrip())
                print(f"OK {name}")
        finally:
            os.chdir(original_cwd)
            _clean_runtime_artifacts(tmp_root)
            _clean_runtime_artifacts(examples_dir)

    print("All examples passed.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run official Sona examples")
    parser.add_argument("--verbose", action="store_true", help="Print each example before running")
    args = parser.parse_args(argv)
    return run_examples(verbose=args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
