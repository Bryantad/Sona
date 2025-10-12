"""Native I/O primitives exposed to higher level stdlib modules."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Tuple


ALLOWED_EXTENSIONS = {
    ".txt",
    ".json",
    ".md",
    ".sona",
    ".py",
    ".js",
    ".ts",
    ".csv",
    ".log",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit
MAX_CONTENT_LENGTH = 1024 * 1024  # 1MB limit for single operations


def _sanitize_prompt(prompt: str) -> str:
    return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", prompt)


def _resolve_path(path: str) -> Tuple[bool, str | str]:
    try:
        candidate = Path(path).expanduser().resolve()
        base = Path.cwd().resolve()
        candidate.relative_to(base)
    except (ValueError, OSError) as exc:
        return False, f"Path outside allowed directory: {exc}"

    if candidate.suffix.lower() not in ALLOWED_EXTENSIONS:
        return False, f"File extension '{candidate.suffix}' not allowed"

    path_str = str(candidate)
    if any(token in path_str for token in ("..", "~", "$", "`")):
        return False, "Suspicious characters in path"

    return True, str(candidate)


def _sanitize_content(content: str | bytes | None) -> str:
    if content is None:
        return ""
    text = str(content)
    if len(text) > MAX_CONTENT_LENGTH:
        text = text[:MAX_CONTENT_LENGTH]
    return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)


def input(prompt: str = "Enter input: ") -> str:
    safe_prompt = _sanitize_prompt(str(prompt))
    return __builtins__["input"](safe_prompt)


def read_file(path: str) -> str | dict[str, str]:
    is_valid, resolved = _resolve_path(path)
    if not is_valid:
        return {"error": resolved}

    try:
        file_size = os.path.getsize(resolved)
        if file_size > MAX_FILE_SIZE:
            return {"error": "File too large to read"}
    except OSError as exc:
        return {"error": f"File not accessible: {exc}"}

    try:
        with open(resolved, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError as exc:
        return {"error": str(exc)}


def write_file(path: str, content: str | bytes) -> bool | dict[str, str]:
    is_valid, resolved = _resolve_path(path)
    if not is_valid:
        return {"error": resolved}

    payload = _sanitize_content(content)
    if len(payload.encode("utf-8")) > MAX_FILE_SIZE:
        return {"error": "Content exceeds maximum file size"}

    try:
        with open(resolved, "w", encoding="utf-8") as handle:
            handle.write(payload)
        return True
    except OSError as exc:
        return {"error": str(exc)}


def append_file(path: str, content: str | bytes) -> bool | dict[str, str]:
    is_valid, resolved = _resolve_path(path)
    if not is_valid:
        return {"error": resolved}

    payload = _sanitize_content(content)
    try:
        current_size = (
            os.path.getsize(resolved) if os.path.exists(resolved) else 0
        )
    except OSError:
        current_size = 0

    new_size = current_size + len(payload.encode("utf-8"))
    if new_size > MAX_FILE_SIZE:
        return {"error": "Appending would exceed maximum file size"}

    try:
        with open(resolved, "a", encoding="utf-8") as handle:
            handle.write(payload)
        return True
    except OSError as exc:
        return {"error": str(exc)}


def stdin_input(prompt: str = "") -> str:
    return input(prompt)


def stdin_read() -> str:
    return input("")


def stdin_write_file(path: str, content: str | bytes) -> bool | dict[str, str]:
    return write_file(path, content)


def stdin_read_file(path: str) -> str | dict[str, str]:
    return read_file(path)


def stdin_write(path: str, content: str | bytes) -> bool | dict[str, str]:
    return write_file(path, content)


def stdin_append(path: str, content: str | bytes) -> bool | dict[str, str]:
    return append_file(path, content)


__all__ = [
    "input",
    "read_file",
    "write_file",
    "append_file",
    "stdin_input",
    "stdin_read",
    "stdin_write_file",
    "stdin_read_file",
    "stdin_write",
    "stdin_append",
]
