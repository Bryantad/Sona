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


def stem(path: str) -> str:
    """Return filename without extension.
    
    Args:
        path: File path
    
    Returns:
        Filename stem
    
    Example:
        stem('/path/to/file.txt')  # 'file'
    """
    return PurePath(path).stem


def with_extension(path: str, new_ext: str) -> str:
    """Replace file extension.
    
    Args:
        path: File path
        new_ext: New extension (with or without dot)
    
    Returns:
        Path with new extension
    
    Example:
        with_extension('file.txt', '.md')  # 'file.md'
    """
    if not new_ext.startswith('.'):
        new_ext = '.' + new_ext
    pure = PurePath(path)
    return str(pure.with_suffix(new_ext))


def with_suffix(path: str, suffix: str) -> str:
    """Add suffix to filename before extension.
    
    Args:
        path: File path
        suffix: Suffix to add
    
    Returns:
        Path with suffix
    
    Example:
        with_suffix('file.txt', '_backup')  # 'file_backup.txt'
    """
    pure = PurePath(path)
    new_name = pure.stem + suffix + pure.suffix
    return str(pure.with_name(new_name))


def relative_to(path: str, base: str) -> str:
    """Compute relative path from base to path.
    
    Args:
        path: Target path
        base: Base path
    
    Returns:
        Relative path
    
    Example:
        relative_to('/a/b/c', '/a')  # 'b/c'
    """
    pure_path = PurePath(path)
    pure_base = PurePath(base)
    try:
        return str(pure_path.relative_to(pure_base))
    except ValueError:
        return path


def is_child_of(path: str, parent: str) -> bool:
    """Check if path is child of parent.
    
    Args:
        path: Child path
        parent: Parent path
    
    Returns:
        True if path is under parent
    
    Example:
        is_child_of('/a/b/c', '/a')  # True
    """
    try:
        PurePath(path).relative_to(parent)
        return True
    except ValueError:
        return False


def common_prefix(paths: Sequence[str]) -> str:
    """Find common prefix of multiple paths.
    
    Args:
        paths: List of paths
    
    Returns:
        Common prefix path
    
    Example:
        common_prefix(['/a/b/c', '/a/b/d'])  # '/a/b'
    """
    if not paths:
        return ""
    
    common = os.path.commonpath(paths)
    return normalize(common)


def expanduser(path: str) -> str:
    """Expand ~ and ~user in path.
    
    Args:
        path: Path with ~ prefix
    
    Returns:
        Expanded path
    
    Example:
        expanduser('~/documents')  # '/home/user/documents'
    """
    return os.path.expanduser(path)


def expandvars(path: str) -> str:
    """Expand environment variables in path.
    
    Args:
        path: Path with $VAR or %VAR% syntax
    
    Returns:
        Expanded path
    
    Example:
        expandvars('$HOME/docs')  # '/home/user/docs'
    """
    return os.path.expandvars(path)


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
    # advanced
    "stem",
    "with_extension",
    "with_suffix",
    "relative_to",
    "is_child_of",
    "common_prefix",
    "expanduser",
    "expandvars",
]
