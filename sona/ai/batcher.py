"""Micro-batching queue (feature gated).

Collects requests that arrive within a short time window and flushes them
as a single list to a user provided ``flush_func``. This is intentionally
minimal and synchronous-friendly: callers block only when waiting for
their own result via ``future.wait()``.

Design goals:
 - Keep zero overhead when disabled (``get_batcher()`` returns ``None``)
 - Avoid external deps / heavy concurrency primitives
 - Deterministic flushing bounded by ``window_ms`` or ``max_batch_size``
 - Simple testability (inject time + flush function)

Limitations / Simplifications:
 - Single global batcher instance (one logical provider pipeline)
 - Thread based timer; no asyncio integration (can be added later)
 - ``flush_func`` must return a list of results (same length) or raise
   an error; mismatches produce per-item errors.
"""
from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..flags import get_flags


ResultList = list[Any]


@dataclass
class _BatchItem:
    payload: Any
    event: threading.Event
    result: Any = None
    error: Exception | None = None

    def set_result(self, value: Any) -> None:
        self.result = value
        self.event.set()

    def set_error(self, exc: Exception) -> None:
        self.error = exc
        self.event.set()


class BatcherFuture:
    """Handle returned to caller allowing them to wait for batch result."""

    def __init__(self, item: _BatchItem):
        self._item = item

    def wait(self, timeout: float | None = None) -> Any:
        self._item.event.wait(timeout)
        if self._item.error:
            raise self._item.error
        return self._item.result

    def done(self) -> bool:
        return self._item.event.is_set()


class Batcher:
    def __init__(
        self,
        window_ms: int,
        flush_func: Callable[[list[Any]], ResultList],
        max_batch_size: int = 32,
        time_func: Callable[[], float] | None = None,
    ):
        self.window_ms = max(0, window_ms)
        self.flush_func = flush_func
        self.max_batch_size = max_batch_size
        self.time = time_func or time.time
        self._lock = threading.Lock()
        self._items: list[_BatchItem] = []
        self._timer: threading.Timer | None = None
        self._flushes = 0
        self._total_items = 0
        self._last_batch_size = 0

    # Public API ---------------------------------------------------------
    def submit(self, payload: Any) -> BatcherFuture:
        item = _BatchItem(payload=payload, event=threading.Event())
        with self._lock:
            self._items.append(item)
            start_timer = False
            if len(self._items) == 1:
                start_timer = True
            if len(self._items) >= self.max_batch_size:
                # Flush immediately; cancel timer if set
                if self._timer:
                    self._timer.cancel()
                    self._timer = None
                self._flush_locked()
            elif start_timer and self.window_ms > 0:
                self._start_timer_locked()
        return BatcherFuture(item)

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "enabled": True,
                "window_ms": self.window_ms,
                "queued": len(self._items),
                "flushes": self._flushes,
                "total_items": self._total_items,
                "last_batch_size": self._last_batch_size,
                "max_batch_size": self.max_batch_size,
            }

    # Internal -----------------------------------------------------------
    def _start_timer_locked(self) -> None:
        delay = self.window_ms / 1000.0
        self._timer = threading.Timer(delay, self._timer_flush)
        self._timer.daemon = True
        self._timer.start()

    def _timer_flush(self) -> None:
        with self._lock:
            self._flush_locked()

    def _flush_locked(self) -> None:
        if not self._items:
            return
        items = self._items
        self._items = []
        self._timer = None
        self._flushes += 1
        self._last_batch_size = len(items)
        self._total_items += len(items)
        payloads = [i.payload for i in items]
        try:
            results = self.flush_func(payloads)
            if len(results) != len(items):  # mismatch -> propagate error
                raise RuntimeError(
                    "flush_func result length mismatch: "
                    f"expected {len(items)} got {len(results)}"
                )
            for it, res in zip(items, results, strict=False):
                it.set_result(res)
        except Exception as exc:  # broad by design (surface batch failure)
            for it in items:
                it.set_error(exc)


_global_batcher: Batcher | None = None


def get_batcher(
    flush_func: Callable[[list[Any]], ResultList] | None = None,
) -> Batcher | None:
    """Return singleton batcher if feature enabled.

    ``flush_func`` is required on first call when creating the instance.
    Subsequent calls may omit it. If batching disabled returns ``None``.
    """
    flags = get_flags()
    if not flags.enable_batching or flags.batch_window_ms <= 0:
        return None
    global _global_batcher
    if _global_batcher is None:
        if flush_func is None:
            raise ValueError("flush_func required on first get_batcher() call")
        _global_batcher = Batcher(flags.batch_window_ms, flush_func)
    return _global_batcher
