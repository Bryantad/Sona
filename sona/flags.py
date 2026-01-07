"""
Feature flag management for Sona.

Reads environment variables and optional persisted preferences to enable
cache/batcher/breaker/capability features.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Flags:
    enable_cache: bool = False
    cache_max_entries: int = 128
    cache_ttl_seconds: int = 600
    enable_batching: bool = False
    batch_window_ms: int = 25
    enable_breaker: bool = False
    breaker_error_rate: float = 0.3
    enable_capabilities: bool = False
    perf_logs: bool = False
    perf_dir: str | None = None


_FLAGS: Flags | None = None


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off", ""}:
        return False
    return default


def _parse_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value.strip())
    except Exception:
        return default


def _parse_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value.strip())
    except Exception:
        return default


def _load_ai_mode_prefs() -> dict:
    try:
        from .persisted_env import load_ai_mode_preferences
    except Exception:
        return {}
    try:
        return load_ai_mode_preferences()
    except Exception:
        return {}


def _load_flags_from_env() -> Flags:
    prefs = _load_ai_mode_prefs()
    enable_cache = _parse_bool(
        os.getenv("SONA_ENABLE_CACHE"),
        bool(prefs.get("enable_cache", False)),
    )
    enable_breaker = _parse_bool(
        os.getenv("SONA_ENABLE_BREAKER"),
        bool(prefs.get("enable_breaker", False)),
    )
    enable_batching = _parse_bool(os.getenv("SONA_ENABLE_BATCH"), False)
    enable_capabilities = _parse_bool(os.getenv("SONA_ENABLE_CAPABILITIES"), False)
    perf_logs = _parse_bool(os.getenv("SONA_PERF_LOGS"), False)

    return Flags(
        enable_cache=enable_cache,
        cache_max_entries=_parse_int(os.getenv("SONA_CACHE_MAX_ENTRIES"), 128),
        cache_ttl_seconds=_parse_int(os.getenv("SONA_CACHE_TTL_SECONDS"), 600),
        enable_batching=enable_batching,
        batch_window_ms=_parse_int(os.getenv("SONA_BATCH_WINDOW_MS"), 25),
        enable_breaker=enable_breaker,
        breaker_error_rate=_parse_float(os.getenv("SONA_BREAKER_ERROR_RATE"), 0.3),
        enable_capabilities=enable_capabilities,
        perf_logs=perf_logs,
        perf_dir=os.getenv("SONA_PERF_DIR"),
    )


def get_flags() -> Flags:
    """Return the cached flags configuration."""
    global _FLAGS
    if _FLAGS is None:
        _FLAGS = _load_flags_from_env()
    return _FLAGS


def refresh_flags() -> Flags:
    """Reload flags from environment and return the updated config."""
    global _FLAGS
    _FLAGS = _load_flags_from_env()
    return _FLAGS


__all__ = ["Flags", "get_flags", "refresh_flags"]
