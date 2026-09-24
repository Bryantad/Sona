"""Versioned typed event/message envelopes with bounded JSON payloads."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

_SAFE_TYPE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")
_FIELD_TYPES = {"string", "integer", "number", "boolean", "object", "array", "null"}


def _validate_timestamp(value: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")


def _payload_size(payload: dict[str, Any]) -> int:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    if any(not isinstance(key, str) for key in payload):
        raise ValueError("payload object keys must be strings")
    try:
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("payload must contain JSON-compatible data") from exc
    return len(encoded.encode("utf-8"))


@dataclass(frozen=True, slots=True)
class EventField:
    name: str
    value_type: str
    required: bool = True

    def __post_init__(self) -> None:
        if not _SAFE_TYPE.fullmatch(self.name):
            raise ValueError("event field name must be a safe identifier")
        if self.value_type not in _FIELD_TYPES:
            raise ValueError(f"unsupported event field type: {self.value_type}")


@dataclass(frozen=True, slots=True)
class EventSchema:
    event_type: str
    version: int
    fields: tuple[EventField, ...]
    maximum_payload_bytes: int = 65536
    allow_unknown_fields: bool = False

    def __post_init__(self) -> None:
        if not _SAFE_TYPE.fullmatch(self.event_type):
            raise ValueError("event_type must be a safe identifier")
        if self.version < 1:
            raise ValueError("event schema version must be positive")
        if not 1 <= self.maximum_payload_bytes <= 65536:
            raise ValueError("maximum_payload_bytes must be between 1 and 65536")
        names = [item.name for item in self.fields]
        if len(names) != len(set(names)):
            raise ValueError("event field names must be unique")

    def validate_payload(self, payload: dict[str, Any]) -> None:
        _payload_size(payload)
        by_name = {item.name: item for item in self.fields}
        missing = [item.name for item in self.fields if item.required and item.name not in payload]
        if missing:
            raise ValueError(f"event payload missing required fields: {', '.join(missing)}")
        unknown = set(payload) - set(by_name)
        if unknown and not self.allow_unknown_fields:
            raise ValueError(f"event payload contains unknown fields: {', '.join(sorted(unknown))}")
        for name, value in payload.items():
            field_spec = by_name.get(name)
            if field_spec is not None and not _matches_type(value, field_spec.value_type):
                raise ValueError(f"event field {name} must be {field_spec.value_type}")
        if _payload_size(payload) > self.maximum_payload_bytes:
            raise ValueError("event payload exceeds maximum_payload_bytes")

    def validate(self, event: EventEnvelope) -> None:
        if event.event_type != self.event_type:
            raise ValueError("event type does not match schema")
        if event.schema_version != self.version:
            raise ValueError("event version does not match schema")
        self.validate_payload(event.payload)


def _matches_type(value: Any, value_type: str) -> bool:
    if value_type == "string":
        return isinstance(value, str)
    if value_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if value_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if value_type == "boolean":
        return isinstance(value, bool)
    if value_type == "object":
        return isinstance(value, dict)
    if value_type == "array":
        return isinstance(value, list)
    return value is None


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    event_type: str
    source: str
    payload: dict[str, Any]
    schema_version: int
    timestamp_utc: str
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not _SAFE_TYPE.fullmatch(self.event_type) or not _SAFE_TYPE.fullmatch(self.source):
            raise ValueError("event_type and source must be safe identifiers")
        if self.schema_version < 1:
            raise ValueError("schema_version must be positive")
        _validate_timestamp(self.timestamp_utc)
        try:
            uuid.UUID(self.event_id)
        except (ValueError, AttributeError) as exc:
            raise ValueError("event_id must be a UUID") from exc
        if _payload_size(self.payload) > 65536:
            raise ValueError("event payload exceeds 65536 bytes")


@dataclass(frozen=True, slots=True)
class MessageEnvelope:
    message_type: str
    payload: dict[str, Any]
    schema_version: int = 1
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        if not _SAFE_TYPE.fullmatch(self.message_type):
            raise ValueError("message_type must be a safe identifier")
        if self.schema_version < 1:
            raise ValueError("schema_version must be positive")
        for name, value in (
            ("message_id", self.message_id),
            ("correlation_id", self.correlation_id),
        ):
            if value is None:
                continue
            try:
                uuid.UUID(value)
            except (ValueError, AttributeError) as exc:
                raise ValueError(f"{name} must be a UUID") from exc
        if _payload_size(self.payload) > 65536:
            raise ValueError("message payload exceeds 65536 bytes")
