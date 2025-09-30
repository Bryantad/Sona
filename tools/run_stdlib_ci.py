"""CI helpers for stdlib scaffolding tasks.

Provides thin wrappers around pytest invocations for fuzz/bench flows and
utility commands for packaging stdlib documentation artifacts.
"""
from __future__ import annotations

import argparse
import importlib
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Iterable


def _run_pytest(marker: str | None = None, keyword: str | None = None) -> int:
    """Execute pytest with optional marker/keyword filters.

    Returns an exit code following pytest semantics, but treats the
    "no tests collected" code (5) as success so CI can tolerate
    yet-to-be-written modules.
    """

    cmd: list[str] = [
        sys.executable,
        "-m",
        "pytest",
        "tests/smod",
        "--maxfail=1",
        "--disable-warnings",
        "-q",
    ]
    if importlib.util.find_spec("pytest_cov") is not None:
        cmd.append("--no-cov")
    if marker:
        cmd.extend(["-m", marker])
    if keyword and keyword.lower() != "all":
        cmd.extend(["-k", keyword])

    print(f"Running pytest command: {' '.join(cmd)}")
    completed = subprocess.run(cmd, check=False)
    code = completed.returncode
    if code == 5:
        print("No tests matched selection; treating as success for CI.")
        return 0
    return code


def cmd_fuzz(targets: list[str]) -> int:
    """Run property-based fuzz suites for the requested targets."""

    if not targets:
        targets = ["all"]
    for target in targets:
        print(f"=== Fuzz target: {target} ===")
        code = _run_pytest(marker="property", keyword=target)
        if code:
            return code
    return 0


def cmd_bench(modules: list[str]) -> int:
    """Run benchmark-tagged tests for selected modules."""

    if not modules:
        modules = ["hash"]
    for module in modules:
        print(f"=== Bench module: {module} ===")
        code = _run_pytest(marker="bench", keyword=module)
        if code:
            return code
    return 0


def cmd_examples_archive(output: Path) -> int:
    """Package stdlib examples into a zip artifact."""

    output.parent.mkdir(parents=True, exist_ok=True)
    examples_root = Path("examples") / "stdlib"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        if examples_root.exists():
            for path in examples_root.rglob("*"):
                if path.is_file():
                    arcname = path.relative_to(Path.cwd())
                    zf.write(path, arcname.as_posix())
        else:
            zf.writestr(
                "README.txt",
                "No stdlib examples found yet. Populate examples/stdlib to "
                "include them in CI artifacts.\n",
            )
    print(f"Wrote stdlib examples archive to {output}")
    return 0


def cmd_clean_artifacts(output_dir: Path) -> int:
    """Remove generated artifact directory if it exists."""

    if output_dir.exists():
        shutil.rmtree(output_dir, ignore_errors=True)
        print(f"Removed artifact directory {output_dir}")
    else:
        print(f"Artifact directory {output_dir} not present; nothing to do.")
    return 0


def _split_csv(arg: str | None) -> list[str]:
    if not arg:
        return []
    return [item.strip() for item in arg.split(",") if item.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stdlib CI helper commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fuzz = subparsers.add_parser(
        "fuzz",
        help="Run property-based fuzz suites",
    )
    fuzz.add_argument(
        "--target",
        help="Comma-separated fuzz targets",
        default="all",
    )

    bench = subparsers.add_parser(
        "bench",
        help="Run benchmark-tagged suites",
    )
    bench.add_argument(
        "--module",
        help="Comma-separated benchmark modules",
        default="hash",
    )

    examples = subparsers.add_parser(
        "examples-archive",
        help="Zip up stdlib examples for CI artifacts",
    )
    examples.add_argument(
        "--output",
        help="Path to write the zip archive",
        default="artifacts/stdlib-examples.zip",
    )

    clean = subparsers.add_parser(
        "clean-artifacts",
        help="Remove the generated artifacts directory",
    )
    clean.add_argument(
        "--output-dir",
        help="Artifacts directory to remove",
        default="artifacts",
    )

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "fuzz":
        return cmd_fuzz(_split_csv(args.target))
    if args.command == "bench":
        return cmd_bench(_split_csv(args.module))
    if args.command == "examples-archive":
        return cmd_examples_archive(Path(args.output))
    if args.command == "clean-artifacts":
        return cmd_clean_artifacts(Path(args.output_dir))

    parser.error(f"Unknown command {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
