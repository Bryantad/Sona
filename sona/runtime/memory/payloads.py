"""Canonical payload normalization for runtime memory episodes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


_SUPPORTED_KINDS = {
    "user_input",
    "interpret_failure",
    "intent_recorded",
    "decision_recorded",
    "focus_transition",
    "goal_continuation_step",
    "goal_state_transition",
    "working_memory_update",
}


@dataclass(frozen=True, slots=True)
class EpisodePayloadSpec:
    required_fields: tuple[str, ...]
    allowed_fields: tuple[str, ...]


_PAYLOAD_SPECS = {
    "user_input": EpisodePayloadSpec(
        required_fields=("filename", "line_count", "text"),
        allowed_fields=("filename", "line_count", "text"),
    ),
    "interpret_failure": EpisodePayloadSpec(
        required_fields=("filename", "error_type", "message"),
        allowed_fields=("filename", "error_type", "message"),
    ),
    "intent_recorded": EpisodePayloadSpec(
        required_fields=("goal", "has_constraints", "has_success"),
        allowed_fields=("goal", "has_constraints", "has_success"),
    ),
    "decision_recorded": EpisodePayloadSpec(
        required_fields=("label", "option", "has_rationale"),
        allowed_fields=("label", "option", "has_rationale"),
    ),
    "focus_transition": EpisodePayloadSpec(
        required_fields=("action", "target", "minutes"),
        allowed_fields=("action", "target", "minutes"),
    ),
    "goal_continuation_step": EpisodePayloadSpec(
        required_fields=("goal_title", "retrieved_count", "next_action"),
        allowed_fields=(
            "goal_title",
            "retrieved_count",
            "next_action",
            "action_type",
            "reason_code",
            "primary_memory_id",
            "inference",
        ),
    ),
    "goal_state_transition": EpisodePayloadSpec(
        required_fields=("goal_title", "from_status", "to_status", "reason"),
        allowed_fields=("goal_title", "from_status", "to_status", "reason"),
    ),
    "working_memory_update": EpisodePayloadSpec(
        required_fields=("action", "key"),
        allowed_fields=("action", "key"),
    ),
}


def normalize_episode_payload(
    kind: str,
    payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Normalize payloads into stable shapes for storage and promotion."""
    payload_dict = dict(payload or {})
    normalized_kind = str(kind).strip()
    if normalized_kind in _SUPPORTED_KINDS:
        return _normalize_supported_payload(normalized_kind, payload_dict)
    return _normalize_generic_payload(payload_dict)


def supported_episode_kinds() -> tuple[str, ...]:
    """Return the set of supported canonical payload kinds."""
    return tuple(sorted(_SUPPORTED_KINDS))


def _normalize_supported_payload(
    kind: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    spec = _PAYLOAD_SPECS[kind]
    for field_name in spec.required_fields:
        if field_name not in payload:
            raise ValueError(
                f"Episode payload for '{kind}' is missing required field "
                f"'{field_name}'"
            )

    allowed_payload = {
        field_name: payload[field_name]
        for field_name in spec.allowed_fields
        if field_name in payload
    }

    if kind == "user_input":
        return {
            "filename": _normalize_text(
                allowed_payload["filename"],
                max_length=240,
            ),
            "line_count": _normalize_non_negative_int(
                allowed_payload["line_count"]
            ),
            "text": _normalize_text(allowed_payload["text"], max_length=240),
        }
    if kind == "interpret_failure":
        return {
            "error_type": _normalize_text(
                allowed_payload["error_type"],
                max_length=120,
            ),
            "filename": _normalize_text(
                allowed_payload["filename"],
                max_length=240,
            ),
            "message": _normalize_text(
                allowed_payload["message"],
                max_length=240,
            ),
        }
    if kind == "intent_recorded":
        return {
            "goal": _normalize_text(allowed_payload["goal"], max_length=160),
            "has_constraints": _normalize_bool(
                allowed_payload["has_constraints"]
            ),
            "has_success": _normalize_bool(allowed_payload["has_success"]),
        }
    if kind == "decision_recorded":
        return {
            "has_rationale": _normalize_bool(allowed_payload["has_rationale"]),
            "label": _normalize_text(allowed_payload["label"], max_length=120),
            "option": _normalize_text(
                allowed_payload["option"],
                max_length=120,
            ),
        }
    if kind == "focus_transition":
        return {
            "action": _normalize_text(
                allowed_payload["action"],
                max_length=40,
            ),
            "minutes": _normalize_optional_int(allowed_payload["minutes"]),
            "target": _normalize_text(
                allowed_payload["target"],
                max_length=120,
            ),
        }
    if kind == "goal_continuation_step":
        normalized = {
            "goal_title": _normalize_text(
                allowed_payload["goal_title"],
                max_length=160,
            ),
            "retrieved_count": _normalize_non_negative_int(
                allowed_payload["retrieved_count"]
            ),
            "next_action": _normalize_text(
                allowed_payload["next_action"],
                max_length=240,
            ),
            "action_type": _normalize_text(
                allowed_payload.get("action_type", ""),
                max_length=80,
            ),
            "reason_code": _normalize_text(
                allowed_payload.get("reason_code", ""),
                max_length=80,
            ),
            "primary_memory_id": _normalize_text(
                allowed_payload.get("primary_memory_id", ""),
                max_length=120,
            ),
        }
        if "inference" in allowed_payload:
            normalized["inference"] = _normalize_json_value(
                allowed_payload["inference"]
            )
        return normalized
    if kind == "goal_state_transition":
        return {
            "goal_title": _normalize_text(
                allowed_payload["goal_title"],
                max_length=160,
            ),
            "from_status": _normalize_text(
                allowed_payload["from_status"],
                max_length=40,
            ),
            "to_status": _normalize_text(
                allowed_payload["to_status"],
                max_length=40,
            ),
            "reason": _normalize_text(
                allowed_payload["reason"],
                max_length=240,
            ),
        }
    if kind == "working_memory_update":
        return {
            "action": _normalize_text(
                allowed_payload["action"],
                max_length=40,
            ),
            "key": _normalize_text(allowed_payload["key"], max_length=120),
        }

    return _normalize_generic_payload(allowed_payload)


def _normalize_generic_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: _normalize_json_value(value)
        for key, value in sorted(
            payload.items(),
            key=lambda item: str(item[0]),
        )
        if value is not None
    }


def _normalize_json_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        return {
            str(key): _normalize_json_value(child)
            for key, child in sorted(
                value.items(),
                key=lambda item: str(item[0]),
            )
            if child is not None
        }
    if isinstance(value, (list, tuple)):
        return [_normalize_json_value(child) for child in value]
    return str(value)


def _normalize_bool(value: Any) -> bool:
    return bool(value)


def _normalize_non_negative_int(value: Any) -> int:
    try:
        normalized = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Expected integer value, got {value!r}") from exc
    if normalized < 0:
        raise ValueError(f"Expected non-negative integer, got {normalized}")
    return normalized


def _normalize_optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return _normalize_non_negative_int(value)


def _normalize_text(value: Any, *, max_length: int) -> str:
    normalized = str(value or "").strip()
    if len(normalized) > max_length:
        return normalized[:max_length]
    return normalized
