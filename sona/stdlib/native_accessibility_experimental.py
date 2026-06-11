"""Runtime-backed experimental cognitive-accessibility helpers.

These APIs are local-only by default. Functions that store session state,
adapt behavior, or persist-like history require explicit opt-in through
`configure({"experimental_accessibility": true})`.
"""

from __future__ import annotations

from datetime import datetime, timezone
import math
import re
from typing import Any


_enabled = False
_state: dict[str, Any] = {
    "interrupts": [],
    "rewards": [],
    "contexts": {},
    "memory": {},
    "anchors": {},
    "shutdown": [],
    "journal": [],
    "adapt": {},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _words(value: Any) -> list[str]:
    return re.findall(r"[A-Za-z0-9_']+", str(value))


def _blocked(action: str) -> dict[str, Any]:
    return {
        "ok": False,
        "requires_opt_in": True,
        "action": action,
        "message": "Set experimental_accessibility to true before using adaptive or state-changing experimental behavior.",
    }


def _is_enabled() -> bool:
    return bool(_enabled)


def experimental_configure(options: Any) -> dict[str, Any]:
    global _enabled
    if isinstance(options, dict) and options.get("experimental_accessibility") is True:
        _enabled = True
    elif isinstance(options, dict) and options.get("experimental_accessibility") is False:
        _enabled = False
    return {"experimental_accessibility": _enabled, "local_only": True}


def experimental_status() -> dict[str, Any]:
    return {"experimental_accessibility": _enabled, "local_only": True}


def interrupt_notice(message: Any, severity: Any = "info") -> dict[str, Any]:
    return {"message": str(message), "severity": str(severity or "info"), "timestamp": _now()}


def interrupt_queue(message: Any, severity: Any = "info") -> dict[str, Any]:
    if not _is_enabled():
        return _blocked("interrupt.queue")
    item = interrupt_notice(message, severity)
    _state["interrupts"].append(item)
    return {"ok": True, "item": item, "count": len(_state["interrupts"])}


def interrupt_list(limit: Any = 20) -> list[dict[str, Any]]:
    return list(_state["interrupts"][-int(limit or 20):])


def hyperfocus_check(minutes: Any, break_interval: Any = 50) -> dict[str, Any]:
    duration = max(0, float(minutes or 0))
    interval = max(1, float(break_interval or 50))
    risk = "high" if duration >= interval * 2 else "watch" if duration >= interval else "ok"
    return {"minutes": duration, "risk": risk, "recommendation": "pause" if risk != "ok" else "continue"}


def hyperfocus_plan(task: Any, minutes: Any = 50) -> list[str]:
    return [f"Focus on {task}.", f"Set a {int(minutes or 50)} minute boundary.", "Stop and check body state."]


def priority_rank(items: Any) -> list[Any]:
    values = list(items or [])

    def score(item: Any) -> float:
        if isinstance(item, dict):
            return float(item.get("priority", item.get("score", 0)))
        return 0.0

    return sorted(values, key=score, reverse=True)


def priority_top(items: Any) -> Any:
    ranked = priority_rank(items)
    return ranked[0] if ranked else None


def drift_detect(events: Any) -> dict[str, Any]:
    values = list(events or [])
    switches = sum(1 for item in values if isinstance(item, dict) and item.get("type") in {"switch", "interrupt"})
    score = min(1.0, switches / max(1, len(values)))
    return {"events": len(values), "switches": switches, "score": round(score, 3), "drift": score >= 0.35}


def drift_reset_prompt(task: Any) -> list[str]:
    return [f"Name current task: {task}", "Close unrelated loop.", "Choose one next action."]


def scaffold_steps(goal: Any, count: Any = 3) -> list[str]:
    total = max(1, int(count or 3))
    return [f"{idx + 1}. {goal} - small step {idx + 1}" for idx in range(total)]


def scaffold_checklist(goal: Any) -> dict[str, Any]:
    return {"goal": str(goal), "steps": scaffold_steps(goal, 3)}


def reentry_card(task: Any, last_step: Any = "", next_step: Any = "") -> dict[str, Any]:
    return {"task": str(task), "last_step": str(last_step or ""), "next_step": str(next_step or "Choose the next visible action.")}


def reentry_prompt(task: Any) -> str:
    return f"Return to {task}: read the last note, then do one small action."


def reward_token(name: Any, points: Any = 1) -> dict[str, Any]:
    return {"name": str(name), "points": int(points or 1), "timestamp": _now()}


def reward_log(name: Any, points: Any = 1) -> dict[str, Any]:
    if not _is_enabled():
        return _blocked("reward.log")
    item = reward_token(name, points)
    _state["rewards"].append(item)
    return {"ok": True, "item": item, "total": sum(entry["points"] for entry in _state["rewards"])}


def context_pack(title: Any, details: Any = None) -> dict[str, Any]:
    return {"title": str(title), "details": details if isinstance(details, dict) else {}, "timestamp": _now()}


def context_save(name: Any, details: Any = None) -> dict[str, Any]:
    if not _is_enabled():
        return _blocked("context.save")
    item = context_pack(name, details)
    _state["contexts"][str(name)] = item
    return {"ok": True, "context": item}


def context_current(name: Any) -> Any:
    return _state["contexts"].get(str(name))


def momentum_score(done: Any, total: Any) -> dict[str, Any]:
    total_i = max(0, int(total or 0))
    done_i = max(0, int(done or 0))
    ratio = 0 if total_i == 0 else min(1.0, done_i / total_i)
    return {"done": done_i, "total": total_i, "percent": round(ratio * 100, 1), "state": "moving" if ratio > 0 else "stalled"}


def momentum_next_action(task: Any) -> str:
    return f"Do the smallest visible part of {task}."


def rotate_plan(items: Any, start: Any = 0) -> list[Any]:
    values = list(items or [])
    if not values:
        return []
    idx = int(start or 0) % len(values)
    return values[idx:] + values[:idx]


def rotate_next(items: Any, current: Any = None) -> Any:
    values = list(items or [])
    if not values:
        return None
    if current not in values:
        return values[0]
    return values[(values.index(current) + 1) % len(values)]


def start_tiny(task: Any) -> dict[str, Any]:
    return {"task": str(task), "action": f"Open the work for {task}.", "minutes": 2}


def start_next(task: Any) -> str:
    return start_tiny(task)["action"]


def alias_create(name: Any, alias: Any) -> dict[str, Any]:
    return {"name": str(name), "alias": str(alias)}


def alias_apply(text: Any, aliases: Any) -> str:
    value = str(text)
    mapping = aliases if isinstance(aliases, dict) else {}
    for source, target in mapping.items():
        value = value.replace(str(source), str(target))
    return value


def phonetic_spell(word: Any) -> list[str]:
    return re.findall(r"[^aeiouy]*[aeiouy]+[^aeiouy]*|[^aeiouy]+$", str(word).lower())


def phonetic_compare(left: Any, right: Any) -> dict[str, Any]:
    l_parts = phonetic_spell(left)
    r_parts = phonetic_spell(right)
    return {"left": l_parts, "right": r_parts, "similar": l_parts == r_parts}


def visual_highlight(text: Any, term: Any) -> dict[str, Any]:
    value = str(text)
    needle = str(term)
    positions = [match.start() for match in re.finditer(re.escape(needle), value, flags=re.IGNORECASE)] if needle else []
    return {"text": value, "term": needle, "positions": positions}


def visual_spacing(text: Any, spaces: Any = 1) -> str:
    gap = " " * max(1, int(spaces or 1))
    return gap.join(_words(text))


def symbol_explain(symbol: Any) -> str:
    mapping = {
        "=": "assignment",
        "==": "equality comparison",
        "!=": "not equal",
        "=>": "maps to",
        "{}": "map or block",
        "[]": "list or index",
    }
    return mapping.get(str(symbol), "No curated symbol explanation is available.")


def symbol_pairs() -> list[dict[str, str]]:
    return [{"symbol": key, "meaning": symbol_explain(key)} for key in ["=", "==", "!=", "=>", "{}", "[]"]]


def sequence_check(items: Any) -> dict[str, Any]:
    values = list(items or [])
    duplicates = sorted({item for item in values if values.count(item) > 1})
    return {"count": len(values), "duplicates": duplicates, "ordered": values == sorted(values)}


def sequence_number(items: Any) -> list[dict[str, Any]]:
    return [{"index": idx + 1, "value": item} for idx, item in enumerate(list(items or []))]


def memory_card(key: Any, value: Any = "") -> dict[str, Any]:
    return {"key": str(key), "value": str(value), "hint": str(value)[:32]}


def memory_store(key: Any, value: Any) -> dict[str, Any]:
    if not _is_enabled():
        return _blocked("memory.store")
    item = memory_card(key, value)
    _state["memory"][str(key)] = item
    return {"ok": True, "item": item}


def memory_recall(key: Any) -> Any:
    return _state["memory"].get(str(key))


def memory_search(query: Any, opts: Any = None) -> dict[str, Any]:
    needle = str(query).lower()
    results = [item for item in _state["memory"].values() if needle in item["key"].lower() or needle in item["value"].lower()]
    return {"query": str(query), "results": results, "local_only": True}


def memory_record(content: Any, opts: Any = None) -> dict[str, Any]:
    key = str((opts or {}).get("key", f"record-{len(_state['memory']) + 1}")) if isinstance(opts, dict) else f"record-{len(_state['memory']) + 1}"
    return memory_store(key, content)


def memory_get_trace(trace_id: Any) -> dict[str, Any]:
    return {"trace_id": str(trace_id), "record": memory_recall(trace_id), "local_only": True}


def memory_reflect(input: Any = None, opts: Any = None) -> dict[str, Any]:
    words = _words(input or "")
    return {"summary": " ".join(words[:12]), "word_count": len(words), "local_only": True}


def contrast_ratio(foreground: Any, background: Any) -> dict[str, Any]:
    def channel(value: str) -> tuple[int, int, int]:
        raw = value.strip().lstrip("#")
        if len(raw) == 3:
            raw = "".join(ch * 2 for ch in raw)
        if len(raw) != 6:
            return (0, 0, 0)
        return tuple(int(raw[idx: idx + 2], 16) for idx in (0, 2, 4))

    def luminance(rgb: tuple[int, int, int]) -> float:
        parts = []
        for item in rgb:
            c = item / 255
            parts.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
        return 0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]

    l1 = luminance(channel(str(foreground)))
    l2 = luminance(channel(str(background)))
    ratio = (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
    return {"ratio": round(ratio, 2), "ok": ratio >= 4.5}


def contrast_recommend(foreground: Any, background: Any) -> str:
    return "contrast ok" if contrast_ratio(foreground, background)["ok"] else "increase contrast"


def template_fill(template: Any, values: Any) -> str:
    result = str(template)
    mapping = values if isinstance(values, dict) else {}
    for key, value in mapping.items():
        result = result.replace("{" + str(key) + "}", str(value))
    return result


def template_checklist(title: Any, items: Any) -> dict[str, Any]:
    return {"title": str(title), "items": [{"text": str(item), "done": False} for item in list(items or [])]}


def spoken_script(text: Any) -> list[str]:
    return [part.strip() for part in re.split(r"[.!?]+", str(text)) if part.strip()]


def spoken_pace(text: Any, words_per_chunk: Any = 8) -> list[str]:
    words = _words(text)
    size = max(1, int(words_per_chunk or 8))
    return [" ".join(words[idx: idx + size]) for idx in range(0, len(words), size)]


def pattern_detect(values: Any) -> dict[str, Any]:
    items = list(values or [])
    if len(items) < 2:
        return {"pattern": [], "repeats": False}
    half = len(items) // 2
    pattern = items[:half]
    return {"pattern": pattern, "repeats": pattern == items[half: half + len(pattern)]}


def pattern_group(values: Any) -> dict[str, list[Any]]:
    groups: dict[str, list[Any]] = {}
    for item in list(values or []):
        groups.setdefault(str(item), []).append(item)
    return groups


def trace_steps(events: Any) -> list[dict[str, Any]]:
    return [{"step": idx + 1, "event": event} for idx, event in enumerate(list(events or []))]


def trace_summary(events: Any) -> str:
    return " -> ".join(str(item) for item in list(events or []))


def transition_plan(source: Any, target: Any) -> list[str]:
    return [f"Close {source}.", "Name what changes.", f"Open {target}.", "Start with one safe step."]


def transition_checklist(source: Any, target: Any) -> dict[str, Any]:
    return {"from": str(source), "to": str(target), "steps": transition_plan(source, target)}


def detail_expand(topic: Any, details: Any = None) -> dict[str, Any]:
    values = details if isinstance(details, dict) else {}
    return {"topic": str(topic), "details": values, "summary": f"{topic}: {len(values)} detail fields"}


def detail_filter(details: Any, keys: Any) -> dict[str, Any]:
    source = details if isinstance(details, dict) else {}
    return {str(key): source.get(key) for key in list(keys or [])}


def anchor_card(name: Any, value: Any) -> dict[str, Any]:
    return {"name": str(name), "value": str(value), "timestamp": _now()}


def anchor_set(name: Any, value: Any) -> dict[str, Any]:
    if not _is_enabled():
        return _blocked("anchor.set")
    item = anchor_card(name, value)
    _state["anchors"][str(name)] = item
    return {"ok": True, "anchor": item}


def anchor_get(name: Any) -> Any:
    return _state["anchors"].get(str(name))


def overload_check(signals: Any) -> dict[str, Any]:
    values = list(signals or [])
    score = min(1.0, len(values) / 5)
    return {"signals": values, "score": round(score, 2), "overloaded": score >= 0.6}


def overload_reduce(signals: Any) -> list[str]:
    return ["lower sensory input", "pause decisions", "choose one safe contact"] if overload_check(signals)["overloaded"] else ["continue gently"]


def mono_focus(task: Any, boundary: Any = "") -> dict[str, Any]:
    return {"task": str(task), "boundary": str(boundary or "one task"), "mode": "single-thread"}


focus = mono_focus


def mono_switch(from_task: Any, to_task: Any) -> list[str]:
    return [f"Park {from_task}.", f"Switch to {to_task}.", "Keep only one active thread."]


switch = mono_switch


def system_map(name: Any, components: Any) -> dict[str, Any]:
    values = list(components or [])
    return {"name": str(name), "components": values, "edges": [{"from": str(name), "to": str(item)} for item in values]}


def system_boundary(name: Any, inputs: Any, outputs: Any) -> dict[str, Any]:
    return {"name": str(name), "inputs": list(inputs or []), "outputs": list(outputs or [])}


def mastery_plan(skill: Any, levels: Any = 3) -> list[dict[str, Any]]:
    count = max(1, int(levels or 3))
    return [{"level": idx + 1, "skill": str(skill), "focus": f"practice slice {idx + 1}"} for idx in range(count)]


def mastery_check(skill: Any, evidence: Any) -> dict[str, Any]:
    items = list(evidence or [])
    return {"skill": str(skill), "evidence_count": len(items), "ready": len(items) >= 3}


def shutdown_plan(cues: Any) -> list[str]:
    return ["stop new input", "reduce sensory load", "use safe routine", *[f"note cue: {cue}" for cue in list(cues or [])]]


def shutdown_log(cues: Any) -> dict[str, Any]:
    if not _is_enabled():
        return _blocked("shutdown.log")
    item = {"timestamp": _now(), "cues": list(cues or []), "plan": shutdown_plan(cues)}
    _state["shutdown"].append(item)
    return {"ok": True, "item": item}


def energy_check(level: Any, capacity: Any = 10) -> dict[str, Any]:
    cap = max(1, float(capacity or 10))
    current = max(0, float(level or 0))
    ratio = min(1.0, current / cap)
    return {"level": current, "capacity": cap, "percent": round(ratio * 100, 1), "state": "low" if ratio < 0.3 else "ok"}


def energy_budget(tasks: Any, level: Any) -> list[Any]:
    values = list(tasks or [])
    return values[: max(0, int(level or 0))]


def narrative_frame(event: Any, meaning: Any = "") -> dict[str, Any]:
    return {"event": str(event), "meaning": str(meaning or ""), "frame": f"What happened: {event}"}


def narrative_steps(event: Any) -> list[str]:
    return [f"Observe: {event}", "Name impact.", "Choose next response."]


def journal_entry(prompt: Any, response: Any = "") -> dict[str, Any]:
    return {"prompt": str(prompt), "response": str(response or ""), "timestamp": _now()}


def journal_save(prompt: Any, response: Any = "") -> dict[str, Any]:
    if not _is_enabled():
        return _blocked("journal.save")
    item = journal_entry(prompt, response)
    _state["journal"].append(item)
    return {"ok": True, "entry": item, "count": len(_state["journal"])}


def journal_recent(limit: Any = 5) -> list[dict[str, Any]]:
    return list(_state["journal"][-int(limit or 5):])


def adapt_suggest(profile: Any, signal: Any) -> dict[str, Any]:
    suggestions = {
        "adhd": "reduce context switches",
        "dyslexia": "increase spacing and chunk text",
        "autism": "make rules explicit",
    }
    return {"profile": str(profile), "signal": str(signal), "suggestion": suggestions.get(str(profile), "use local explicit preferences")}


def adapt_set_preferences(name: Any, preferences: Any) -> dict[str, Any]:
    if not _is_enabled():
        return _blocked("adapt.set_preferences")
    _state["adapt"][str(name)] = preferences if isinstance(preferences, dict) else {"value": preferences}
    return {"ok": True, "name": str(name), "preferences": _state["adapt"][str(name)]}


def adapt_get_preferences(name: Any) -> Any:
    return _state["adapt"].get(str(name))


__all__ = [name for name in globals() if not name.startswith("_")]
