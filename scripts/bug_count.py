#!/usr/bin/env python3
"""
Language-agnostic bug marker counter.
Scans text files for TODO/FIXME/BUG-style markers and reports totals.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
from typing import Dict, Iterable, List, Tuple


DEFAULT_MARKERS = ["TODO", "FIXME", "BUG", "HACK", "XXX"]
DEFAULT_IGNORES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "node_modules",
    "dist",
    "build",
    "out",
    "coverage",
    "reports",
    "lsp",
}


def _is_binary(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            chunk = handle.read(8192)
        return b"\x00" in chunk
    except OSError:
        return True


def _walk_files(root: Path, ignore_dirs: Iterable[str], max_size: int) -> Iterable[Path]:
    ignore_set = {name.lower() for name in ignore_dirs}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            name for name in dirnames if name.lower() not in ignore_set
        ]
        for filename in filenames:
            path = Path(dirpath) / filename
            try:
                if path.stat().st_size > max_size:
                    continue
            except OSError:
                continue
            yield path


def _compile_patterns(markers: List[str]) -> Dict[str, re.Pattern]:
    patterns = {}
    for marker in markers:
        patterns[marker] = re.compile(rf"\\b{re.escape(marker)}\\b", re.IGNORECASE)
    return patterns


def _scan_file(path: Path, patterns: Dict[str, re.Pattern]) -> Dict[str, int]:
    counts: Dict[str, int] = {marker: 0 for marker in patterns}
    if _is_binary(path):
        return counts
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                for marker, pattern in patterns.items():
                    matches = pattern.findall(line)
                    if matches:
                        counts[marker] += len(matches)
    except OSError:
        return counts
    return counts


def _aggregate_counts(
    root: Path, markers: List[str], ignore_dirs: Iterable[str], max_size: int
) -> Tuple[Dict[str, int], Dict[str, int], int]:
    patterns = _compile_patterns(markers)
    totals = {marker: 0 for marker in markers}
    by_file: Dict[str, int] = {}
    files_scanned = 0

    for path in _walk_files(root, ignore_dirs, max_size):
        files_scanned += 1
        file_counts = _scan_file(path, patterns)
        file_total = sum(file_counts.values())
        if file_total:
            rel_path = str(path.relative_to(root))
            by_file[rel_path] = file_total
            for marker, count in file_counts.items():
                totals[marker] += count

    return totals, by_file, files_scanned


def _parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Count TODO/FIXME/BUG markers across a codebase."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Root directory to scan (default: current directory).",
    )
    parser.add_argument(
        "--markers",
        default=",".join(DEFAULT_MARKERS),
        help="Comma-separated markers to count (default: TODO,FIXME,BUG,HACK,XXX).",
    )
    parser.add_argument(
        "--ignore",
        default=",".join(sorted(DEFAULT_IGNORES)),
        help="Comma-separated directory names to skip.",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=1_000_000,
        help="Skip files larger than this size in bytes (default: 1,000,000).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top files to show (default: 10).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of text.",
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = _parse_args(argv)
    root = Path(args.root).resolve()
    markers = [m.strip() for m in args.markers.split(",") if m.strip()]
    ignore_dirs = [d.strip() for d in args.ignore.split(",") if d.strip()]

    totals, by_file, files_scanned = _aggregate_counts(
        root, markers, ignore_dirs, args.max_size
    )
    total_hits = sum(totals.values())
    top_files = sorted(by_file.items(), key=lambda item: item[1], reverse=True)[: args.top]

    if args.json:
        payload = {
            "root": str(root),
            "files_scanned": files_scanned,
            "total_hits": total_hits,
            "by_marker": totals,
            "top_files": top_files,
        }
        print(json.dumps(payload, indent=2))
        return 0

    print(f"Bug marker scan: {total_hits} hits across {files_scanned} files")
    for marker in markers:
        print(f"- {marker}: {totals.get(marker, 0)}")

    if top_files:
        print("\nTop files:")
        for path, count in top_files:
            print(f"- {path}: {count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(os.sys.argv[1:]))
