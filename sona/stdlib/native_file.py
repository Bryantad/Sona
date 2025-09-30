"""Low level file helpers used by higher level stdlib modules."""

from __future__ import annotations

from pathlib import Path


def read(path: str, encoding: str = "utf-8") -> str | None:
    try:
        with open(path, "r", encoding=encoding) as handle:
            return handle.read()
    except FileNotFoundError:
        return None
    except OSError as exc:
        return f"[file error] {exc}"


def write(path: str, content: str, encoding: str = "utf-8") -> bool | str:
    try:
        with open(path, "w", encoding=encoding) as handle:
            handle.write(content)
        return True
    except OSError as exc:
        return f"[file error] {exc}"


def append(path: str, content: str, encoding: str = "utf-8") -> bool | str:
    try:
        with open(path, "a", encoding=encoding) as handle:
            handle.write(content)
        return True
    except OSError as exc:
        return f"[file error] {exc}"


def exists(path: str) -> bool:
    return Path(path).exists()


__all__ = ["read", "write", "append", "exists"]
