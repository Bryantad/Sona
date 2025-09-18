"""Feature flag and environment configuration for Sona 0.9.3.

New subsystems (cache, batching, circuit breaker, perf logging,
policy, capabilities) are gated by environment variables so they
can be enabled incrementally. Defaults keep new behavior OFF to
avoid destabilizing existing flows.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


# Environment variable names (public surface)
ENV_CACHE_TTL = "SONA_CACHE_TTL"          # e.g. "30s"
ENV_CACHE_MAX = "SONA_CACHE_MAX"          # int
ENV_BATCH_WINDOW_MS = "SONA_BATCH_WINDOW_MS"
ENV_BREAKER_ERR_RATE = "SONA_BREAKER_ERR_RATE"
ENV_PERF_LOGS = "SONA_PERF_LOGS"          # 1 enables perf logging
ENV_PERF_DIR = "SONA_PERF_DIR"            # directory for perf logs
ENV_POLICY_PATH = "SONA_POLICY_PATH"      # path to .sona-policy.json
ENV_STREAMING_ENABLED = "SONA_STREAMING_ENABLED"  # '1' to enable streaming

# Feature master toggles (simple on/off)
ENV_ENABLE_CACHE = "SONA_ENABLE_CACHE"
ENV_ENABLE_BATCHING = "SONA_ENABLE_BATCHING"
ENV_ENABLE_BREAKER = "SONA_ENABLE_BREAKER"
ENV_ENABLE_CAPABILITIES = "SONA_ENABLE_CAPABILITIES"  # ai_plan / ai_review

_DEFAULTS = {
    ENV_CACHE_TTL: "0s",           # disabled unless >0
    ENV_CACHE_MAX: "128",          # baseline size
    ENV_BATCH_WINDOW_MS: "25",     # conservative default
    ENV_BREAKER_ERR_RATE: "0.3",   # open threshold
    ENV_PERF_LOGS: "0",            # disabled
    ENV_PERF_DIR: ".",             # current dir by default
    ENV_POLICY_PATH: ".sona-policy.json",
    ENV_STREAMING_ENABLED: "1",
    ENV_ENABLE_CACHE: "0",
    ENV_ENABLE_BATCHING: "0",
    ENV_ENABLE_BREAKER: "0",
    ENV_ENABLE_CAPABILITIES: "0",
}


def _get(name: str) -> str:
    return os.environ.get(name, _DEFAULTS[name])


def _parse_seconds(spec: str) -> float:
    try:
        spec = spec.strip().lower()
        if spec.endswith("ms"):
            return float(spec[:-2]) / 1000.0
        if spec.endswith("s"):
            return float(spec[:-1])
        return float(spec)  # assume seconds
    except Exception:
        return 0.0


@dataclass(frozen=True)
class FeatureFlags:
    enable_cache: bool
    enable_batching: bool
    enable_breaker: bool
    enable_capabilities: bool
    streaming_enabled: bool
    cache_ttl_seconds: float
    cache_max_entries: int
    batch_window_ms: int
    breaker_error_rate: float
    perf_logs: bool
    perf_dir: str
    policy_path: str

    @classmethod
    def load(cls) -> FeatureFlags:
        return cls(
            enable_cache=_get(ENV_ENABLE_CACHE) == "1",
            enable_batching=_get(ENV_ENABLE_BATCHING) == "1",
            enable_breaker=_get(ENV_ENABLE_BREAKER) == "1",
            enable_capabilities=_get(ENV_ENABLE_CAPABILITIES) == "1",
            streaming_enabled=_get(ENV_STREAMING_ENABLED) == "1",
            cache_ttl_seconds=_parse_seconds(_get(ENV_CACHE_TTL)),
            cache_max_entries=int(_get(ENV_CACHE_MAX) or 0),
            batch_window_ms=int(_get(ENV_BATCH_WINDOW_MS) or 0),
            breaker_error_rate=float(_get(ENV_BREAKER_ERR_RATE) or 0.0),
            perf_logs=_get(ENV_PERF_LOGS) == "1",
            perf_dir=_get(ENV_PERF_DIR),
            policy_path=_get(ENV_POLICY_PATH),
        )


_FLAGS: FeatureFlags | None = None


def get_flags() -> FeatureFlags:
    global _FLAGS
    if _FLAGS is None:
        _FLAGS = FeatureFlags.load()
    return _FLAGS


def refresh_flags() -> FeatureFlags:
    global _FLAGS
    _FLAGS = FeatureFlags.load()
    return _FLAGS
