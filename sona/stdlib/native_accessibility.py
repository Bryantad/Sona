"""Native backing for Sona cognitive-accessibility `.smod` modules.

All state is process-local. No function persists data unless a future explicit
storage option is added and enabled by the caller.
"""

from __future__ import annotations

from datetime import datetime, timezone
import math
import re
import textwrap
import time
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _call(fn: Any, *args: Any) -> Any:
    if hasattr(fn, "call"):
        return fn.call(list(args), {})
    return fn(*args)


def _words(value: Any) -> list[str]:
    return [word for word in re.split(r"\s+", str(value).strip()) if word]


_breadcrumbs: list[dict[str, Any]] = []
_flow_options: dict[str, Any] = {"max_switches": 5, "max_errors": 3}
_pace_mode = "balanced"
_pace_options: dict[str, Any] = {}
_affirm_enabled = True
_checkpoints: dict[str, Any] = {}
_timers: list[dict[str, Any]] = []
_active_timer: dict[str, Any] | None = None
_noise_level = "normal"
_noise_allowed: set[str] = set()
_noise_blocked: set[str] = set()
_tone_mode = "neutral"
_readability_options: dict[str, Any] = {"max_identifier_length": 32}
_linewidth = 80
_chunk_read_sections: list[Any] = []
_chunk_read_index = 0
_boundaries: dict[str, dict[str, Any]] = {}
_active_boundary: str | None = None
_routines: dict[str, list[Any]] = {}
_active_routine: dict[str, Any] | None = None
_strict_enabled = False
_strict_options: dict[str, Any] = {}
_certainty_items: list[dict[str, Any]] = []
_sensory_enabled = False
_sensory_options: dict[str, Any] = {}


def simplify_message(text: Any, level: Any = "standard") -> str:
    value = str(text).strip()
    mode = str(level or "standard")
    if mode == "brief":
        return value.split(".")[0].strip()
    if mode == "beginner":
        return f"What happened: {value}"
    return value


def simplify_error(error_value: Any, level: Any = "standard") -> str:
    if isinstance(error_value, dict):
        text = error_value.get("message") or error_value.get("error") or str(error_value)
    else:
        text = str(error_value)
    return simplify_message(text, level)


def simplify_steps(error_value: Any) -> list[str]:
    return [
        "Read the error message.",
        "Check the named file or module.",
        "Run the smallest relevant test again.",
    ]


def breadcrumb_add(message: Any, fields: Any = None) -> dict[str, Any]:
    record = {"timestamp": _now(), "message": str(message), "fields": fields if isinstance(fields, dict) else {}}
    _breadcrumbs.append(record)
    return dict(record)


def breadcrumb_current() -> dict[str, Any] | None:
    return dict(_breadcrumbs[-1]) if _breadcrumbs else None


def breadcrumb_history(limit: Any = 20) -> list[dict[str, Any]]:
    return [dict(item) for item in _breadcrumbs[-int(limit or 20):]]


def breadcrumb_clear() -> bool:
    _breadcrumbs.clear()
    return True


def breadcrumb_format(mode: Any = "plain") -> str:
    if str(mode) == "json":
        import json
        return json.dumps(_breadcrumbs, sort_keys=True)
    return "\n".join(f"- {item['message']}" for item in _breadcrumbs)


def flow_score(metrics: Any) -> float:
    data = metrics if isinstance(metrics, dict) else {}
    switches = float(data.get("context_switches", 0))
    errors = float(data.get("errors", 0))
    completed = float(data.get("completed_steps", 0))
    score = 1.0 - min(1.0, (switches / 10.0) + (errors / 10.0)) + min(0.25, completed / 20.0)
    return round(max(0.0, min(1.0, score)), 3)


def flow_check(metrics: Any) -> dict[str, Any]:
    score = flow_score(metrics)
    return {"score": score, "ok": score >= 0.6}


def flow_suggest(metrics: Any) -> list[str]:
    score = flow_score(metrics)
    if score >= 0.8:
        return ["Continue current workflow."]
    return ["Reduce context switches.", "Work on one next visible step."]


def flow_configure(options: Any) -> dict[str, Any]:
    if isinstance(options, dict):
        _flow_options.update(options)
    return dict(_flow_options)


def explain_value(value: Any) -> str:
    return f"{type(value).__name__}: {value!r}"


def explain_error(error_value: Any) -> str:
    return simplify_error(error_value)


def explain_module(name: Any) -> str:
    return f"Module `{name}` is discovered from the local Sona standard library manifest."


def explain_function(name: Any) -> str:
    return f"Function `{name}` is a callable runtime value."


def explain_steps(value_or_error: Any) -> list[str]:
    return simplify_steps(value_or_error)


def pace_set(mode: Any) -> str:
    global _pace_mode
    candidate = str(mode)
    if candidate not in {"compact", "balanced", "guided", "low-stimulation"}:
        raise ValueError(f"Unsupported pace mode: {mode}")
    _pace_mode = candidate
    return _pace_mode


def pace_current() -> str:
    return _pace_mode


def pace_configure(options: Any) -> dict[str, Any]:
    if isinstance(options, dict):
        _pace_options.update(options)
    return {"mode": _pace_mode, "options": dict(_pace_options)}


def pace_format(text: Any) -> str:
    value = str(text)
    if _pace_mode == "compact":
        return value.split("\n")[0]
    if _pace_mode in {"guided", "low-stimulation"}:
        return "\n".join(f"- {line}" for line in value.splitlines() if line.strip())
    return value


def affirm_success(message: Any, fields: Any = None) -> dict[str, Any]:
    return {"enabled": _affirm_enabled, "type": "success", "message": str(message), "fields": fields if isinstance(fields, dict) else {}}


def affirm_milestone(name: Any, details: Any = "") -> dict[str, Any]:
    return {"enabled": _affirm_enabled, "type": "milestone", "name": str(name), "details": str(details or "")}


def affirm_enabled() -> bool:
    return _affirm_enabled


def affirm_enable() -> bool:
    global _affirm_enabled
    _affirm_enabled = True
    return _affirm_enabled


def affirm_disable() -> bool:
    global _affirm_enabled
    _affirm_enabled = False
    return _affirm_enabled


def chunk_items(values: Any, size: Any = 5) -> list[list[Any]]:
    count = max(1, int(size or 5))
    items = list(values or [])
    return [items[idx: idx + count] for idx in range(0, len(items), count)]


def chunk_text(value: Any, width: Any = 80) -> list[str]:
    return textwrap.wrap(str(value), width=max(1, int(width or 80)))


def chunk_steps(values: Any, size: Any = 3) -> list[list[Any]]:
    return chunk_items(values, size or 3)


def chunk_progress(current: Any, total: Any) -> dict[str, Any]:
    total_f = float(total or 0)
    ratio = 0.0 if total_f <= 0 else max(0.0, min(1.0, float(current) / total_f))
    return {"current": current, "total": total, "percent": round(ratio * 100, 1)}


def chunk_checkpoint(name: Any, state: Any = None) -> dict[str, Any]:
    _checkpoints[str(name)] = state if isinstance(state, dict) else {"value": state}
    return {"name": str(name), "state": _checkpoints[str(name)]}


def chunk_resume(name: Any) -> Any:
    return _checkpoints.get(str(name))


def timer_start(name: Any, minutes: Any) -> dict[str, Any]:
    global _active_timer
    _active_timer = {
        "name": str(name),
        "seconds": float(minutes) * 60.0,
        "started": time.monotonic(),
        "paused_at": None,
        "paused_total": 0.0,
    }
    return {"name": _active_timer["name"], "minutes": float(minutes)}


def _timer_elapsed() -> float:
    if not _active_timer:
        return 0.0
    end = _active_timer["paused_at"] if _active_timer["paused_at"] else time.monotonic()
    return max(0.0, end - _active_timer["started"] - _active_timer["paused_total"])


def timer_remaining() -> float:
    if not _active_timer:
        return 0.0
    return max(0.0, _active_timer["seconds"] - _timer_elapsed())


def timer_elapsed() -> float:
    return _timer_elapsed()


def timer_check() -> dict[str, Any]:
    return {
        "active": _active_timer is not None,
        "paused": bool(_active_timer and _active_timer["paused_at"] is not None),
        "elapsed": timer_elapsed(),
        "remaining": timer_remaining(),
    }


def timer_pause() -> dict[str, Any]:
    if _active_timer and _active_timer["paused_at"] is None:
        _active_timer["paused_at"] = time.monotonic()
    return timer_check()


def timer_resume() -> dict[str, Any]:
    if _active_timer and _active_timer["paused_at"] is not None:
        _active_timer["paused_total"] += time.monotonic() - _active_timer["paused_at"]
        _active_timer["paused_at"] = None
    return timer_check()


def timer_stop(summary: Any = "") -> dict[str, Any] | None:
    global _active_timer
    if not _active_timer:
        return None
    record = {"name": _active_timer["name"], "elapsed": timer_elapsed(), "summary": str(summary or "")}
    _timers.append(record)
    _active_timer = None
    return record


def timer_history() -> list[dict[str, Any]]:
    return list(_timers)


def noise_set_level(level: Any) -> str:
    global _noise_level
    candidate = str(level)
    if candidate not in {"minimal", "focused", "normal", "verbose"}:
        raise ValueError(f"Unsupported noise level: {level}")
    _noise_level = candidate
    return _noise_level


def noise_current_level() -> str:
    return _noise_level


def noise_filter(events: Any) -> list[Any]:
    items = list(events or [])
    if _noise_level == "verbose":
        return items
    return [item for item in items if str(item if not isinstance(item, dict) else item.get("scope", item)) not in _noise_blocked]


def noise_allow(scope: Any) -> bool:
    _noise_allowed.add(str(scope))
    _noise_blocked.discard(str(scope))
    return True


def noise_block(scope: Any) -> bool:
    _noise_blocked.add(str(scope))
    return True


def noise_reset() -> bool:
    global _noise_level
    _noise_level = "normal"
    _noise_allowed.clear()
    _noise_blocked.clear()
    return True


def tone_neutralize(message: Any) -> str:
    text = str(message)
    text = re.sub(r"\bobviously\b", "", text, flags=re.IGNORECASE)
    return re.sub(r"[!]+", ".", text).strip()


def tone_set(mode: Any) -> str:
    global _tone_mode
    candidate = str(mode)
    if candidate not in {"neutral", "direct", "supportive"}:
        raise ValueError(f"Unsupported tone mode: {mode}")
    _tone_mode = candidate
    return _tone_mode


def tone_current() -> str:
    return _tone_mode


def readability_score(text: Any) -> dict[str, Any]:
    words = _words(text)
    avg = sum(len(word) for word in words) / len(words) if words else 0.0
    score = max(0, 100 - int(avg * 8) - max(0, len(words) - 40))
    return {"score": score, "word_count": len(words), "average_word_length": round(avg, 2)}


def readability_identifier(name: Any) -> dict[str, Any]:
    value = str(name)
    issues = []
    if len(value) > int(_readability_options.get("max_identifier_length", 32)):
        issues.append("long")
    if re.search(r"[Il1O0]{2,}", value):
        issues.append("ambiguous-characters")
    if re.search(r"[a-z][A-Z][a-z][A-Z]", value):
        issues.append("mixed-casing")
    return {"name": value, "issues": issues, "ok": not issues}


def readability_suggest(name: Any) -> list[str]:
    report = readability_identifier(name)
    suggestions = []
    if "long" in report["issues"]:
        suggestions.append("Use fewer words or a shorter noun phrase.")
    if "ambiguous-characters" in report["issues"]:
        suggestions.append("Avoid repeated I/l/1/O/0 sequences.")
    if "mixed-casing" in report["issues"]:
        suggestions.append("Use consistent snake_case or camelCase.")
    return suggestions


def readability_check_many(names: Any) -> list[dict[str, Any]]:
    return [readability_identifier(name) for name in list(names or [])]


def readability_configure(options: Any) -> dict[str, Any]:
    if isinstance(options, dict):
        _readability_options.update(options)
    return dict(_readability_options)


def linewidth_set(width: Any) -> int:
    global _linewidth
    _linewidth = max(20, int(width))
    return _linewidth


def linewidth_current() -> int:
    return _linewidth


def linewidth_wrap(text: Any) -> str:
    return "\n".join(textwrap.wrap(str(text), width=_linewidth))


def linewidth_check(text: Any) -> dict[str, Any]:
    lines = str(text).splitlines() or [str(text)]
    too_long = [idx + 1 for idx, line in enumerate(lines) if len(line) > _linewidth]
    return {"ok": not too_long, "too_long": too_long, "width": _linewidth}


def mirror_pairs() -> list[dict[str, str]]:
    return [
        {"left": "=", "right": "==", "meaning": "assignment versus equality"},
        {"left": "!", "right": "!=", "meaning": "not versus not-equal"},
        {"left": "<", "right": "<=", "meaning": "less-than versus less-or-equal"},
        {"left": ">", "right": ">=", "meaning": "greater-than versus greater-or-equal"},
        {"left": "()", "right": "[]", "meaning": "call/grouping versus indexing/list"},
        {"left": "[]", "right": "{}", "meaning": "list/indexing versus map/block"},
    ]


def mirror_check(source: Any) -> list[dict[str, str]]:
    text = str(source)
    return [pair for pair in mirror_pairs() if pair["left"] in text and pair["right"] in text]


def mirror_explain(symbol: Any) -> str:
    value = str(symbol)
    for pair in mirror_pairs():
        if value in {pair["left"], pair["right"]}:
            return pair["meaning"]
    return "No curated explanation is available for this symbol."


def chunk_read_text(value: Any, size: Any = 5) -> list[str]:
    words = _words(value)
    count = max(1, int(size or 5))
    return [" ".join(words[idx: idx + count]) for idx in range(0, len(words), count)]


def chunk_read_sections(values: Any) -> list[Any]:
    global _chunk_read_sections, _chunk_read_index
    _chunk_read_sections = list(values or [])
    _chunk_read_index = 0
    return list(_chunk_read_sections)


def chunk_read_current() -> Any:
    if not _chunk_read_sections:
        return None
    return _chunk_read_sections[_chunk_read_index]


def chunk_read_next() -> Any:
    global _chunk_read_index
    if not _chunk_read_sections:
        return None
    _chunk_read_index = min(len(_chunk_read_sections) - 1, _chunk_read_index + 1)
    return chunk_read_current()


def chunk_read_previous() -> Any:
    global _chunk_read_index
    if not _chunk_read_sections:
        return None
    _chunk_read_index = max(0, _chunk_read_index - 1)
    return chunk_read_current()


def chunk_read_reset() -> bool:
    global _chunk_read_index
    _chunk_read_index = 0
    return True


class ContractFailure(AssertionError):
    pass


def contract_require(condition: Any, message: Any) -> bool:
    if not condition:
        raise ContractFailure(str(message))
    return True


def contract_ensure(condition: Any, message: Any) -> bool:
    return contract_require(condition, message)


def contract_type(value: Any, expected: Any, name: Any = "") -> bool:
    expected_name = str(expected).lower()
    actual = type(value).__name__
    aliases = {
        "number": {"int", "float"},
        "integer": {"int"},
        "string": {"str"},
        "text": {"str"},
        "list": {"list"},
        "array": {"list", "tuple"},
        "map": {"dict"},
        "dict": {"dict"},
        "boolean": {"bool"},
        "bool": {"bool"},
    }
    expected_names = aliases.get(expected_name, {expected_name})
    if actual.lower() not in expected_names:
        raise ContractFailure(f"{name or 'value'} expected {expected_name}, got {actual}")
    return True


def contract_range(value: Any, minimum: Any, maximum: Any, name: Any = "") -> bool:
    number = float(value)
    if number < float(minimum) or number > float(maximum):
        raise ContractFailure(f"{name or 'value'} outside range {minimum}..{maximum}")
    return True


def contract_non_empty(value: Any, name: Any = "") -> bool:
    if not value:
        raise ContractFailure(f"{name or 'value'} must be non-empty")
    return True


def contract_equal(actual: Any, expected: Any, message: Any = "") -> bool:
    if actual != expected:
        raise ContractFailure(str(message or f"Expected {expected!r}, got {actual!r}"))
    return True


def boundary_create(name: Any, permissions: Any) -> dict[str, Any]:
    key = str(name)
    _boundaries[key] = {"name": key, "allowed": set(permissions or []), "denied": set()}
    return boundary_current_named(key)


def boundary_current_named(name: str) -> dict[str, Any]:
    item = _boundaries[name]
    return {"name": item["name"], "allowed": sorted(item["allowed"]), "denied": sorted(item["denied"])}


def boundary_activate(name: Any) -> dict[str, Any]:
    global _active_boundary
    key = str(name)
    if key not in _boundaries:
        raise ValueError(f"Unknown boundary: {name}")
    _active_boundary = key
    return boundary_current()


def boundary_current() -> dict[str, Any] | None:
    return boundary_current_named(_active_boundary) if _active_boundary else None


def boundary_check(permission: Any, target: Any = "") -> bool:
    if not _active_boundary:
        return True
    item = _boundaries[_active_boundary]
    perm = str(permission)
    if perm in item["denied"]:
        return False
    return perm in item["allowed"]


def boundary_allow(permission: Any, target: Any = "") -> bool:
    if not _active_boundary:
        raise ValueError("No active boundary")
    item = _boundaries[_active_boundary]
    item["allowed"].add(str(permission))
    item["denied"].discard(str(permission))
    return True


def boundary_deny(permission: Any, target: Any = "") -> bool:
    if not _active_boundary:
        raise ValueError("No active boundary")
    item = _boundaries[_active_boundary]
    item["denied"].add(str(permission))
    return True


def boundary_deactivate() -> bool:
    global _active_boundary
    _active_boundary = None
    return True


def routine_define(name: Any, steps: Any) -> dict[str, Any]:
    _routines[str(name)] = list(steps or [])
    return {"name": str(name), "steps": list(_routines[str(name)])}


def routine_start(name: Any) -> dict[str, Any]:
    global _active_routine
    key = str(name)
    if key not in _routines:
        raise ValueError(f"Unknown routine: {name}")
    _active_routine = {"name": key, "steps": list(_routines[key]), "index": 0, "complete": False}
    return routine_current()


def routine_next(step: Any = None) -> dict[str, Any] | None:
    if not _active_routine:
        return None
    if step is not None and _active_routine["index"] < len(_active_routine["steps"]):
        _active_routine["steps"][_active_routine["index"]] = step
    _active_routine["index"] += 1
    if _active_routine["index"] >= len(_active_routine["steps"]):
        _active_routine["complete"] = True
    return routine_current()


def routine_current() -> dict[str, Any] | None:
    if not _active_routine:
        return None
    current_step = None
    if _active_routine["index"] < len(_active_routine["steps"]):
        current_step = _active_routine["steps"][_active_routine["index"]]
    return {**_active_routine, "current_step": current_step}


def routine_complete() -> dict[str, Any] | None:
    if not _active_routine:
        return None
    _active_routine["complete"] = True
    _active_routine["index"] = len(_active_routine["steps"])
    return routine_current()


def routine_reset() -> bool:
    global _active_routine
    _active_routine = None
    return True


def strict_enable() -> bool:
    global _strict_enabled
    _strict_enabled = True
    return True


def strict_disable() -> bool:
    global _strict_enabled
    _strict_enabled = False
    return False


def strict_is_enabled() -> bool:
    return _strict_enabled


def strict_configure(options: Any) -> dict[str, Any]:
    if isinstance(options, dict):
        _strict_options.update(options)
    return dict(_strict_options)


def strict_check(event: Any) -> dict[str, Any]:
    warnings = []
    data = event if isinstance(event, dict) else {"event": event}
    if data.get("side_effect") and not data.get("boundary"):
        warnings.append("side-effect without explicit boundary")
    return {"enabled": _strict_enabled, "warnings": warnings, "ok": not warnings}


def certainty_check(value_or_metadata: Any) -> dict[str, Any]:
    data = value_or_metadata if isinstance(value_or_metadata, dict) else {"value": value_or_metadata}
    severity = "info" if data.get("source") or data.get("value") is not None else "warning"
    return {"severity": severity, "metadata": data}


def certainty_report() -> list[dict[str, Any]]:
    return list(_certainty_items)


def certainty_add(name: Any, description: Any, severity: Any = "info") -> dict[str, Any]:
    item = {"name": str(name), "description": str(description), "severity": str(severity or "info")}
    _certainty_items.append(item)
    return dict(item)


def certainty_clear() -> bool:
    _certainty_items.clear()
    return True


def sensory_enable() -> bool:
    global _sensory_enabled
    _sensory_enabled = True
    return True


def sensory_disable() -> bool:
    global _sensory_enabled
    _sensory_enabled = False
    return False


def sensory_is_enabled() -> bool:
    return _sensory_enabled


def sensory_configure(options: Any) -> dict[str, Any]:
    if isinstance(options, dict):
        _sensory_options.update(options)
    return dict(_sensory_options)


def sensory_apply(text: Any) -> str:
    value = str(text)
    if not _sensory_enabled:
        return value
    value = re.sub(r"\x1b\[[0-9;]*m", "", value)
    value = re.sub(r"([.!?]){2,}", r"\1", value)
    return value.strip()


__all__ = [name for name in globals() if not name.startswith("_")]
