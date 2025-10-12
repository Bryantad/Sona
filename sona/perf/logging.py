"""Performance event logging (feature gated).

Writes JSONL lines to a daily-rotated file when perf logging flag is on.
File naming: ``perf-YYYYMMDD.jsonl`` in current working directory.
Usage (lightweight):
    from sona.perf.logging import log_perf
    log_perf("ai_request", duration_ms=123, model="gpt4o")

I/O errors are swallowed to avoid impacting primary flows.
"""
from __future__ import annotations

import json
import threading
import time
from contextlib import suppress
from typing import Any

from ..flags import get_flags
from pathlib import Path


_lock = threading.Lock()
_current_day: str | None = None
_file_handle: Any | None = None
_current_day: str | None = None
_file_handle: Any | None = None


def _day_str(ts: float) -> str:
    return time.strftime("%Y%m%d", time.localtime(ts))


def _ensure_file(ts: float) -> None:
    global _current_day, _file_handle
    day = _day_str(ts)
    if _current_day == day and _file_handle is not None:
        return
    # Rotate
    if _file_handle is not None:
        with suppress(Exception):
            _file_handle.close()
        _file_handle = None
    flags = get_flags()
    base_dir = Path(flags.perf_dir or ".")
    try:
        base_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        base_dir = Path(".")
    filename = str(base_dir / f"perf-{day}.jsonl")
    try:
        # Need to keep file handle open for performance logging
        _file_handle = open(filename, "a", encoding="utf-8")  # noqa: SIM115
        _current_day = day
    except Exception:
        _file_handle = None


def log_perf(event: str, **fields: Any) -> None:
    flags = get_flags()
    if not flags.perf_logs:
        return
    ts = time.time()
    record = {"ts": ts, "event": event}
    record.update(fields)
    line = json.dumps(record, ensure_ascii=False)
    with _lock:
        _ensure_file(ts)
        if _file_handle is None:
            return
        try:
            _file_handle.write(line + "\n")
            _file_handle.flush()
        except Exception:
            pass


def close_logs() -> None:
    global _file_handle
    with _lock:
        if _file_handle is not None:
            with suppress(Exception):
                _file_handle.close()
            _file_handle = None
