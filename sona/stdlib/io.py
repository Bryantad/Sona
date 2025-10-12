"""Sona standard library: high level file I/O helpers."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

try:  # pragma: no cover - allow running outside package
    from . import native_io  # type: ignore
except ImportError:  # pragma: no cover
    import native_io  # type: ignore


def input(prompt: str = "") -> str:
    return native_io.input(prompt)


def read_file(path: str) -> str:
    return native_io.read_file(path)


def write_file(path: str, content: str) -> bool | str:
    return native_io.write_file(path, content)


def read(path: str, encoding: str = "utf-8") -> str:
    """Return the entire file contents as a string."""

    with open(path, "r", encoding=encoding) as handle:
        return handle.read()


def write(path: str, content: str, encoding: str = "utf-8") -> None:
    """Overwrite a file with *content*."""

    with open(path, "w", encoding=encoding) as handle:
        handle.write(content)


def append(path: str, content: str, encoding: str = "utf-8") -> None:
    """Append *content* to an existing file."""

    with open(path, "a", encoding=encoding) as handle:
        handle.write(content)


def exists(path: str) -> bool:
    return Path(path).exists()


def isfile(path: str) -> bool:
    return Path(path).is_file()


def isdir(path: str) -> bool:
    return Path(path).is_dir()


def remove(path: str) -> None:
    target = Path(path)
    if target.is_dir() and not target.is_symlink():
        shutil.rmtree(target)
    else:
        target.unlink(missing_ok=True)


def mkdir(path: str, parents: bool = True, exist_ok: bool = True) -> None:
    Path(path).mkdir(parents=parents, exist_ok=exist_ok)


def listdir(path: str) -> list[str]:
    return os.listdir(path)


def copy(src: str, dst: str) -> None:
    shutil.copy(src, dst)


__all__ = [
    "input",
    "read_file",
    "write_file",
    "read",
    "write",
    "append",
    "exists",
    "isfile",
    "isdir",
    "remove",
    "mkdir",
    "listdir",
    "copy",
]
