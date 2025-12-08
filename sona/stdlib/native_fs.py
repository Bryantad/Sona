"""Native glue exposing :mod:`sona.stdlib.fs` to the Sona runtime."""

from __future__ import annotations

from typing import Optional

from . import fs as _fs


def fs_read(path: str, encoding: str | None = "utf-8") -> str:
    return _fs.read(path, encoding=encoding or "utf-8")


def fs_read_bytes(path: str) -> bytes:
    return _fs.read_bytes(path)


def fs_write(
    path: str,
    content: str,
    encoding: str | None = "utf-8",
) -> int:
    return _fs.write(path, content, encoding=encoding or "utf-8")


def fs_write_bytes(path: str, data: bytes) -> int:
    return _fs.write_bytes(path, data)


def fs_append(
    path: str,
    content: str,
    encoding: str | None = "utf-8",
) -> int:
    return _fs.append(path, content, encoding=encoding or "utf-8")


def fs_exists(path: str) -> bool:
    return _fs.exists(path)


def fs_is_file(path: str) -> bool:
    return _fs.is_file(path)


def fs_is_dir(path: str) -> bool:
    return _fs.is_dir(path)


def fs_list_dir(path: str, recursive: bool = False) -> list[str]:
    return _fs.list_dir(path, recursive=recursive)


def fs_mkdir(path: str, parents: bool = True, exist_ok: bool = True) -> str:
    return _fs.mkdir(path, parents=parents, exist_ok=exist_ok)


def fs_remove(path: str, recursive: bool = True) -> bool:
    return _fs.remove(path, recursive=recursive)


def fs_copy(src: str, dst: str, overwrite: bool = True) -> str:
    return _fs.copy(src, dst, overwrite=overwrite)


def fs_move(src: str, dst: str, overwrite: bool = True) -> str:
    return _fs.move(src, dst, overwrite=overwrite)


def fs_touch(path: str, exist_ok: bool = True) -> str:
    return _fs.touch(path, exist_ok=exist_ok)


def fs_chmod(path: str, mode: int | str) -> bool:
    return _fs.chmod(path, mode)


def fs_stat(path: str) -> dict:
    return _fs.stat(path)


def fs_symlink(target: str, link_path: str, exist_ok: bool = False) -> bool:
    return _fs.symlink(target, link_path, exist_ok=exist_ok)


def fs_readlink(path: str) -> Optional[str]:
    return _fs.readlink(path)


def fs_watch(
    path: str,
    timeout_ms: int = 1000,
    interval_ms: int = 100,
) -> Optional[dict]:
    return _fs.watch(path, timeout_ms=timeout_ms, interval_ms=interval_ms)


def fs_set_times(
    path: str,
    access_time: float | None = None,
    modified_time: float | None = None,
) -> bool:
    return _fs.set_times(
        path,
        access_time=access_time,
        modified_time=modified_time,
    )


def fs_glob(pattern: str, recursive: bool = False) -> list[str]:
    return _fs.glob(pattern, recursive=recursive)


def fs_find_files(path: str, pattern: str = "*", recursive: bool = True) -> list[str]:
    return _fs.find_files(path, pattern=pattern, recursive=recursive)


def fs_disk_usage(path: str) -> dict:
    return _fs.disk_usage(path)


def fs_get_size(path: str, follow_symlinks: bool = True) -> int:
    return _fs.get_size(path, follow_symlinks=follow_symlinks)


def fs_rename(src: str, dst: str) -> str:
    return _fs.rename(src, dst)


def fs_read_lines(path: str, encoding: str | None = "utf-8") -> list[str]:
    return _fs.read_lines(path, encoding=encoding or "utf-8")


def fs_write_lines(path: str, lines: list[str], encoding: str | None = "utf-8") -> int:
    return _fs.write_lines(path, lines, encoding=encoding or "utf-8")


def fs_is_empty(path: str) -> bool:
    return _fs.is_empty(path)


def fs_walk(path: str) -> list[dict]:
    return _fs.walk(path)


def fs_temp_file(suffix: str = "", prefix: str = "tmp", dir: str | None = None) -> str:
    return _fs.temp_file(suffix=suffix, prefix=prefix, dir=dir)


def fs_temp_dir(prefix: str = "tmp", dir: str | None = None) -> str:
    return _fs.temp_dir(prefix=prefix, dir=dir)


__all__ = [
    "fs_read",
    "fs_read_bytes",
    "fs_write",
    "fs_write_bytes",
    "fs_append",
    "fs_exists",
    "fs_is_file",
    "fs_is_dir",
    "fs_list_dir",
    "fs_mkdir",
    "fs_remove",
    "fs_copy",
    "fs_move",
    "fs_touch",
    "fs_chmod",
    "fs_stat",
    "fs_symlink",
    "fs_readlink",
    "fs_watch",
    "fs_set_times",
    "fs_glob",
    "fs_find_files",
    "fs_disk_usage",
    "fs_get_size",
    "fs_rename",
    "fs_read_lines",
    "fs_write_lines",
    "fs_is_empty",
    "fs_walk",
    "fs_temp_file",
    "fs_temp_dir",
]
