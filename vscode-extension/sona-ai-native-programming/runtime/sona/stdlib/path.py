"""High-level path utilities for the Sona standard library."""

from __future__ import annotations

import os
from pathlib import PurePath
from typing import Iterable, Sequence


def _ensure_sequence(
    parts: Sequence[str] | Iterable[str] | str,
) -> Sequence[str]:
    if isinstance(parts, str):
        return [parts]
    if isinstance(parts, Sequence):
        return [str(part) for part in parts]
    return [str(part) for part in list(parts)]


def join(parts: Sequence[str] | Iterable[str] | str) -> str:
    """Join multiple path segments, preserving platform-specific separators."""

    segments = _ensure_sequence(parts)
    if not segments:
        return "."
    return normalize(os.path.join(*segments))


def normalize(path: str) -> str:
    """Collapse redundant separators and up-level references in *path*."""

    if path == "":
        return "."
    return os.path.normpath(path)


def basename(path: str) -> str:
    """Return the final component of *path*."""

    return os.path.basename(path)


def dirname(path: str) -> str:
    """Return the directory portion of *path*."""

    return os.path.dirname(path)


def split(path: str) -> dict[str, object]:
    """Split *path* into drive/root information and individual parts."""

    pure = PurePath(path)
    return {
        "drive": getattr(pure, "drive", ""),
        "root": pure.root,
        "parts": [str(part) for part in pure.parts],
        "is_absolute": os.path.isabs(path),
    }


def extension(path: str) -> str:
    """Return the file extension (with leading dot) or an empty string."""

    return os.path.splitext(path)[1]


def is_absolute(path: str) -> bool:
    """Return True if *path* is absolute."""

    return os.path.isabs(path)


def is_relative(path: str) -> bool:
    """Return True if *path* is relative."""

    return not os.path.isabs(path)


def resolve(base: str, target: str) -> str:
    """Resolve *target* against *base* without touching the filesystem."""

    if is_absolute(target):
        return normalize(target)
    if base == "":
        return normalize(target)
    return normalize(os.path.join(base, target))


def _clean_segments(path: str) -> list[str]:
    pure = PurePath(path)
    return [str(part) for part in pure.parts]


__all__ = [
    "join",
    "normalize",
    "basename",
    "dirname",
    "split",
    "extension",
    "is_absolute",
    "is_relative",
    "resolve",
]
