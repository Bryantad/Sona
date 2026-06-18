"""Native backing for the public Sona `profile` accessibility module.

Profile state is process-local and optional. Profile names are presets, not
diagnoses, and no state is persisted by this module.
"""

from __future__ import annotations

from typing import Any

from . import native_accessibility as _accessibility


_AVAILABLE = [
    "cross-profile",
    "adhd",
    "dyslexia",
    "autism",
    "low-stimulation",
    "custom",
]
_BASELINE = {
    "pace_mode": "balanced",
    "noise_level": "normal",
    "linewidth": 80,
    "max_identifier_length": 32,
    "strict": False,
    "sensory": False,
    "flow": {"max_switches": 5, "max_errors": 3},
}
_PRESETS: dict[str, dict[str, Any]] = {
    "cross-profile": {
        "pace_mode": "guided",
        "flow": {"max_switches": 4, "max_errors": 2},
    },
    "adhd": {
        "pace_mode": "guided",
        "noise_level": "focused",
        "flow": {"max_switches": 3, "max_errors": 2},
    },
    "dyslexia": {
        "pace_mode": "guided",
        "linewidth": 72,
        "max_identifier_length": 24,
    },
    "autism": {
        "pace_mode": "guided",
        "strict": True,
        "sensory": True,
    },
    "low-stimulation": {
        "pace_mode": "low-stimulation",
        "noise_level": "minimal",
        "sensory": True,
    },
    "custom": {},
}
_PACE_MODES = {"compact", "balanced", "guided", "low-stimulation"}
_NOISE_LEVELS = {"minimal", "focused", "normal", "verbose"}
_active: list[str] = []
_options: dict[str, Any] = {}


def _normalize_name(name: Any) -> str:
    candidate = str(name).strip().lower()
    if candidate not in _AVAILABLE:
        raise ValueError(f"Unsupported profile preset: {name}")
    return candidate


def _as_bool(value: Any, field: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ValueError(f"profile option `{field}` must be true or false")


def _as_int(value: Any, field: str, minimum: int) -> int:
    if isinstance(value, bool):
        raise ValueError(f"profile option `{field}` must be an integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"profile option `{field}` must be an integer") from exc
    if number < minimum:
        raise ValueError(f"profile option `{field}` must be at least {minimum}")
    return number


def _validate_flow(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("profile option `flow` must be a map")
    normalized: dict[str, Any] = {}
    for key, item in value.items():
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"profile flow option `{key}` must be a number")
        if item < 0:
            raise ValueError(f"profile flow option `{key}` must be non-negative")
        normalized[str(key)] = item
    return normalized


def _validate_options(options: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(options)
    if "pace_mode" in normalized:
        mode = str(normalized["pace_mode"])
        if mode not in _PACE_MODES:
            raise ValueError(f"Unsupported profile pace_mode: {mode}")
        normalized["pace_mode"] = mode
    if "noise_level" in normalized:
        level = str(normalized["noise_level"])
        if level not in _NOISE_LEVELS:
            raise ValueError(f"Unsupported profile noise_level: {level}")
        normalized["noise_level"] = level
    if "linewidth" in normalized:
        normalized["linewidth"] = _as_int(normalized["linewidth"], "linewidth", 20)
    if "max_identifier_length" in normalized:
        normalized["max_identifier_length"] = _as_int(
            normalized["max_identifier_length"],
            "max_identifier_length",
            1,
        )
    if "strict" in normalized:
        normalized["strict"] = _as_bool(normalized["strict"], "strict")
    if "sensory" in normalized:
        normalized["sensory"] = _as_bool(normalized["sensory"], "sensory")
    if "flow" in normalized:
        normalized["flow"] = _validate_flow(normalized["flow"])
    return normalized


def _merge_runtime(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    if "flow" in base:
        merged["flow"] = dict(base["flow"])
    for key, value in update.items():
        if key == "flow":
            flow = dict(merged.get("flow", {}))
            flow.update(value)
            merged["flow"] = flow
        elif key in {
            "pace_mode",
            "noise_level",
            "linewidth",
            "max_identifier_length",
            "strict",
            "sensory",
        }:
            merged[key] = value
    return merged


def _profile_runtime_config() -> dict[str, Any]:
    config = _merge_runtime(_BASELINE, {})
    for name in _active:
        config = _merge_runtime(config, _PRESETS[name])
    config = _merge_runtime(config, _validate_options(_options))
    return config


def _reset_accessibility_runtime() -> None:
    _accessibility.pace_set(_BASELINE["pace_mode"])
    _accessibility._pace_options.clear()
    _accessibility.noise_reset()
    _accessibility.linewidth_set(_BASELINE["linewidth"])
    _accessibility._readability_options.clear()
    _accessibility._readability_options.update(
        {"max_identifier_length": _BASELINE["max_identifier_length"]}
    )
    _accessibility.strict_disable()
    _accessibility._strict_options.clear()
    _accessibility.sensory_disable()
    _accessibility._sensory_options.clear()
    _accessibility._flow_options.clear()
    _accessibility._flow_options.update(_BASELINE["flow"])


def _apply_accessibility_runtime(config: dict[str, Any]) -> None:
    _reset_accessibility_runtime()
    _accessibility.pace_set(config["pace_mode"])
    _accessibility.noise_set_level(config["noise_level"])
    _accessibility.linewidth_set(config["linewidth"])
    _accessibility.readability_configure(
        {"max_identifier_length": config["max_identifier_length"]}
    )
    _accessibility._flow_options.clear()
    _accessibility._flow_options.update(config["flow"])
    if config["strict"]:
        _accessibility.strict_enable()
    else:
        _accessibility.strict_disable()
    if config["sensory"]:
        _accessibility.sensory_enable()
    else:
        _accessibility.sensory_disable()


def _runtime_snapshot() -> dict[str, Any]:
    return {
        "pace_mode": _accessibility.pace_current(),
        "noise_level": _accessibility.noise_current_level(),
        "linewidth": _accessibility.linewidth_current(),
        "readability": _accessibility.readability_configure({}),
        "strict_enabled": _accessibility.strict_is_enabled(),
        "sensory_enabled": _accessibility.sensory_is_enabled(),
        "flow": _accessibility.flow_configure({}),
    }


def _reapply() -> None:
    _apply_accessibility_runtime(_profile_runtime_config())


def profile_activate(name: Any) -> dict[str, Any]:
    candidate = _normalize_name(name)
    _active.clear()
    _active.append(candidate)
    _reapply()
    return profile_current()


def profile_activate_many(names: Any) -> dict[str, Any]:
    if not isinstance(names, list):
        raise ValueError("profiles must be a list")
    selected = []
    for name in names:
        candidate = _normalize_name(name)
        if candidate not in selected:
            selected.append(candidate)
    _active[:] = selected
    _reapply()
    return profile_current()


def profile_current() -> dict[str, Any]:
    return {
        "active": list(_active),
        "options": dict(_options),
        "runtime": _runtime_snapshot(),
        "local_only": True,
        "persistent": False,
    }


def profile_available() -> list[str]:
    return list(_AVAILABLE)


def profile_reset() -> dict[str, Any]:
    _active.clear()
    _options.clear()
    _reset_accessibility_runtime()
    return profile_current()


def profile_configure(options: Any) -> dict[str, Any]:
    if not isinstance(options, dict):
        raise ValueError("profile options must be a map")
    normalized = _validate_options(options)
    _options.update(normalized)
    _reapply()
    return profile_current()


__all__ = [
    "profile_activate",
    "profile_activate_many",
    "profile_current",
    "profile_available",
    "profile_reset",
    "profile_configure",
]
