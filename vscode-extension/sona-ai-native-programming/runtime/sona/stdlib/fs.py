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


def rmdir(path: str) -> bool:
    return remove(path, recursive=False)


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


def glob(pattern: str, *, recursive: bool = False) -> List[str]:
    """Find files matching glob pattern.

    Args:
        pattern: Glob pattern (e.g., '*.txt', '**/*.py')
        recursive: Enable recursive globbing

    Returns:
        List of matching file paths

    Example:
        files = glob('*.txt')
        py_files = glob('**/*.py', recursive=True)
    """
    from glob import glob as _glob
    return [str(p) for p in _glob(pattern, recursive=recursive)]


def find_files(
    path: str,
    pattern: str = "*",
    *,
    recursive: bool = True,
) -> List[str]:
    """Find files in directory matching pattern.

    Args:
        path: Directory to search
        pattern: Filename pattern
        recursive: Search subdirectories

    Returns:
        List of matching file paths

    Example:
        txt_files = find_files('/data', '*.txt')
    """
    root = Path(path)
    if not root.exists():
        return []

    if recursive:
        matches = root.rglob(pattern)
    else:
        matches = root.glob(pattern)

    return [str(p) for p in matches if p.is_file()]


def disk_usage(path: str) -> Dict[str, int]:
    """Get disk usage statistics.

    Args:
        path: Path to check

    Returns:
        Dict with 'total', 'used', 'free' in bytes

    Example:
        usage = disk_usage('/')
        print(usage['free'])
    """
    usage = shutil.disk_usage(path)
    return {
        "total": usage.total,
        "used": usage.used,
        "free": usage.free,
    }


def get_size(path: str, *, follow_symlinks: bool = True) -> int:
    """Get file/directory size in bytes.

    Args:
        path: File or directory path
        follow_symlinks: Follow symbolic links

    Returns:
        Size in bytes

    Example:
        size = get_size('/path/to/file.txt')
    """
    target = Path(path)
    if not target.exists():
        return 0

    if target.is_file():
        return target.stat().st_size

    total = 0
    for entry in target.rglob("*"):
        if entry.is_file():
            total += entry.stat().st_size
    return total


def rename(src: str, dst: str) -> str:
    """Rename file or directory.

    Args:
        src: Source path
        dst: Destination path

    Returns:
        New path

    Example:
        new_path = rename('old.txt', 'new.txt')
    """
    source = Path(src)
    target = Path(dst)
    source.rename(target)
    return str(target)


def read_lines(path: str, encoding: str = "utf-8") -> List[str]:
    """Read file as list of lines.

    Args:
        path: File path
        encoding: Text encoding

    Returns:
        List of lines (newlines preserved)

    Example:
        lines = read_lines('data.txt')
    """
    with open(path, "r", encoding=encoding) as f:
        return f.readlines()


def write_lines(
    path: str,
    lines: List[str],
    encoding: str = "utf-8",
) -> int:
    """Write list of lines to file.

    Args:
        path: File path
        lines: List of lines
        encoding: Text encoding

    Returns:
        Number of bytes written

    Example:
        write_lines('data.txt', ['line1\\n', 'line2\\n'])
    """
    parent = Path(path).parent
    if parent and not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding=encoding) as f:
        return f.writelines(lines) or sum(len(line) for line in lines)


def is_empty(path: str) -> bool:
    """Check if file/directory is empty.

    Args:
        path: Path to check

    Returns:
        True if empty, False otherwise

    Example:
        if is_empty('/path/to/dir'):
            print('Directory is empty')
    """
    target = Path(path)
    if not target.exists():
        return True

    if target.is_file():
        return target.stat().st_size == 0

    return not any(target.iterdir())


def walk(path: str) -> List[Dict[str, object]]:
    """Walk directory tree.

    Args:
        path: Root directory

    Returns:
        List of dicts with 'root', 'dirs', 'files'

    Example:
        for entry in walk('/path'):
            print(entry['root'], entry['files'])
    """
    result = []
    for root, dirs, files in os.walk(path):
        result.append({
            "root": root,
            "dirs": dirs,
            "files": files,
        })
    return result


def temp_file(
    suffix: str = "",
    prefix: str = "tmp",
    dir: Optional[str] = None,
) -> str:
    """Create temporary file.

    Args:
        suffix: Filename suffix
        prefix: Filename prefix
        dir: Directory (default: system temp)

    Returns:
        Path to temporary file

    Example:
        tmp = temp_file(suffix='.txt')
        write(tmp, 'data')
    """
    import tempfile
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
    os.close(fd)
    return path


def temp_dir(prefix: str = "tmp", dir: Optional[str] = None) -> str:
    """Create a temporary directory and return its path."""
    import tempfile

    return tempfile.mkdtemp(prefix=prefix, dir=dir)


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
    # advanced
    "glob",
    "find_files",
    "disk_usage",
    "get_size",
    "rename",
    "read_lines",
    "write_lines",
    "is_empty",
    "walk",
    "temp_file",
    "temp_dir",
]
