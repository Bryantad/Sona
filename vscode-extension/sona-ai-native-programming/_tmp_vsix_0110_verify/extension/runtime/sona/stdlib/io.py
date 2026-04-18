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


def read_bytes(path: str) -> bytes:
    """Read file as bytes.
    
    Args:
        path: File path
    
    Returns:
        File contents as bytes
    
    Example:
        data = read_bytes('image.png')
    """
    with open(path, "rb") as f:
        return f.read()


def write_bytes(path: str, data: bytes) -> None:
    """Write bytes to file.
    
    Args:
        path: File path
        data: Bytes to write
    
    Example:
        write_bytes('image.png', b'\\x89PNG...')
    """
    with open(path, "wb") as f:
        f.write(data)


def read_lines(path: str, encoding: str = "utf-8") -> list[str]:
    """Read file as list of lines.
    
    Args:
        path: File path
        encoding: Text encoding
    
    Returns:
        List of lines (with newlines)
    
    Example:
        lines = read_lines('data.txt')
    """
    with open(path, "r", encoding=encoding) as f:
        return f.readlines()


def write_lines(
    path: str,
    lines: list[str],
    encoding: str = "utf-8",
) -> None:
    """Write list of lines to file.
    
    Args:
        path: File path
        lines: List of lines
        encoding: Text encoding
    
    Example:
        write_lines('data.txt', ['line1\\n', 'line2\\n'])
    """
    with open(path, "w", encoding=encoding) as f:
        f.writelines(lines)


def move(src: str, dst: str) -> None:
    """Move file or directory.
    
    Args:
        src: Source path
        dst: Destination path
    
    Example:
        move('old.txt', 'new.txt')
    """
    shutil.move(src, dst)


def size(path: str) -> int:
    """Get file size in bytes.
    
    Args:
        path: File path
    
    Returns:
        File size in bytes
    
    Example:
        bytes_count = size('file.txt')
    """
    return Path(path).stat().st_size


def print_to_file(
    path: str,
    *values,
    sep: str = " ",
    end: str = "\n",
    encoding: str = "utf-8",
) -> None:
    """Print values to file.
    
    Args:
        path: File path
        values: Values to print
        sep: Separator between values
        end: End character
        encoding: Text encoding
    
    Example:
        print_to_file('log.txt', 'Hello', 'World')
    """
    with open(path, "a", encoding=encoding) as f:
        print(*values, sep=sep, end=end, file=f)


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
    # advanced
    "read_bytes",
    "write_bytes",
    "read_lines",
    "write_lines",
    "move",
    "size",
    "print_to_file",
]
