"""File system helpers backing the Sona stdlib ``fs`` module."""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional


def read(path: str, encoding: str = "utf-8") -> str:
    with open(path, "r", encoding=encoding) as handle:
        return handle.read()


def read_bytes(path: str) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


def write(path: str, content: str, encoding: str = "utf-8") -> int:
    parent = Path(path).parent
    if parent and not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding=encoding) as handle:
        written = handle.write(content)
    return written


def write_bytes(path: str, data: bytes) -> int:
    parent = Path(path).parent
    if parent and not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as handle:
        written = handle.write(data)
    return written


def append(path: str, content: str, encoding: str = "utf-8") -> int:
    with open(path, "a", encoding=encoding) as handle:
        written = handle.write(content)
    return written


def exists(path: str) -> bool:
    return Path(path).exists()


def is_file(path: str) -> bool:
    return Path(path).is_file()


def is_dir(path: str) -> bool:
    return Path(path).is_dir()


def list_dir(path: str, *, recursive: bool = False) -> List[str]:
    root = Path(path)
    if not recursive:
        return [entry.name for entry in root.iterdir()]
    results: List[str] = []
    for entry in root.rglob("*"):
        results.append(str(entry.relative_to(root)))
    return results


def mkdir(path: str, *, parents: bool = True, exist_ok: bool = True) -> str:
    Path(path).mkdir(parents=parents, exist_ok=exist_ok)
    return str(Path(path))


def remove(path: str, *, recursive: bool = True) -> bool:
    target = Path(path)
    try:
        if target.is_dir() and recursive:
            shutil.rmtree(target)
        elif target.is_dir():
            target.rmdir()
        elif target.exists():
            target.unlink()
        else:
            return False
        return True
    except OSError:
        return False


def copy(src: str, dst: str, *, overwrite: bool = True) -> str:
    source = Path(src)
    target = Path(dst)
    if target.exists() and not overwrite:
        raise FileExistsError(dst)
    if source.is_dir():
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return str(target)


def move(src: str, dst: str, *, overwrite: bool = True) -> str:
    target = Path(dst)
    if target.exists():
        if overwrite:
            remove(str(target))
        else:
            raise FileExistsError(dst)
    shutil.move(src, dst)
    return str(Path(dst))


def touch(path: str, *, exist_ok: bool = True) -> str:
    target = Path(path)
    if target.exists() and not exist_ok:
        raise FileExistsError(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.touch()
    return str(target)


def chmod(path: str, mode: int | str) -> bool:
    try:
        value = int(mode, 8) if isinstance(mode, str) else int(mode)
        os.chmod(path, value)
        return True
    except (OSError, ValueError):
        return False


def stat(path: str) -> Dict[str, object]:
    target = Path(path)
    if not target.exists():
        return {
            "path": str(target),
            "exists": False,
        }
    info = target.lstat()
    return {
        "path": str(target),
        "exists": True,
        "is_file": target.is_file(),
        "is_dir": target.is_dir(),
        "is_symlink": target.is_symlink(),
        "size": info.st_size,
        "mode": info.st_mode,
        "permissions": format(info.st_mode & 0o777, "o"),
        "mtime": info.st_mtime,
        "ctime": info.st_ctime,
        "atime": info.st_atime,
    }


def symlink(target: str, link_path: str, *, exist_ok: bool = False) -> bool:
    link = Path(link_path)
    try:
        if link.exists() and not exist_ok:
            raise FileExistsError(link_path)
        if link.exists():
            remove(str(link))
        os.symlink(target, link_path)
        return True
    except (OSError, NotImplementedError):
        return False


def readlink(path: str) -> Optional[str]:
    try:
        return os.readlink(path)
    except OSError:
        return None


def _snapshot(path: Path) -> Dict[str, object]:
    # Be robust to races: the file can be deleted between exists() and stat().
    try:
        if not path.exists():
            return {"exists": False}
        info = path.stat()
        return {
            "exists": True,
            "size": info.st_size,
            "mtime": info.st_mtime,
            "mode": info.st_mode,
        }
    except (FileNotFoundError, OSError):
        # If the target disappears mid-check, treat as not existing.
        return {"exists": False}


def _detect_change(
    previous: Dict[str, object],
    current: Dict[str, object],
) -> Optional[Dict[str, object]]:
    if previous.get("exists") and not current.get("exists"):
        return {"event": "deleted", "after": current}
    if not previous.get("exists") and current.get("exists"):
        return {"event": "created", "after": current}
    if previous.get("exists") and current.get("exists"):
        if (
            previous.get("size") != current.get("size")
            or previous.get("mtime") != current.get("mtime")
            or previous.get("mode") != current.get("mode")
        ):
            return {
                "event": "modified",
                "before": previous,
                "after": current,
            }
    return None


def watch(
    path: str,
    timeout_ms: int = 1000,
    interval_ms: int = 100,
) -> Optional[Dict[str, object]]:
    target = Path(path)
    start = time.monotonic()
    timeout = timeout_ms / 1000.0
    interval = max(0.01, interval_ms / 1000.0)
    previous = _snapshot(target)

    while time.monotonic() - start < timeout:
        time.sleep(interval)
        current = _snapshot(target)
        change = _detect_change(previous, current)
        if change:
            change["path"] = str(target)
            return change
    return None


def set_times(
    path: str,
    *,
    access_time: float | None = None,
    modified_time: float | None = None,
) -> bool:
    try:
        # If both times are None, use current time
        if access_time is None and modified_time is None:
            times = None
        else:
            # Use current time for any None values
            current_time = time.time()
            times = (
                access_time if access_time is not None else current_time,
                modified_time if modified_time is not None else current_time,
            )
        os.utime(path, times=times)
        return True
    except OSError:
        return False


__all__ = [
    "read",
    "read_bytes",
    "write",
    "write_bytes",
    "append",
    "exists",
    "is_file",
    "is_dir",
    "list_dir",
    "mkdir",
    "remove",
    "copy",
    "move",
    "touch",
    "chmod",
    "stat",
    "symlink",
    "readlink",
    "watch",
    "set_times",
]
