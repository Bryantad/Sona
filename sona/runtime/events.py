"""Versioned typed event/message envelopes with bounded JSON payloads."""

from __future__ import annotations

import json
import math
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

_SAFE_TYPE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")
_FIELD_TYPES = {"string", "integer", "number", "boolean", "object", "array", "null"}
_MAX_PAYLOAD_BYTES = 65_536
_MAX_ENVELOPE_BYTES = _MAX_PAYLOAD_BYTES + 2_048


def _positive_version(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")


def _validate_json_value(value: Any, path: str = "payload") -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("payload must contain finite JSON-compatible numbers")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("payload object keys must be strings")
            _validate_json_value(item, f"{path}.{key}")
        return
    raise ValueError("payload must contain JSON-compatible data")


def _payload_size(payload: dict[str, Any]) -> int:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    try:
        _validate_json_value(payload)
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        return len(encoded.encode("utf-8"))
    except (RecursionError, TypeError, UnicodeError, ValueError) as exc:
        if isinstance(exc, ValueError) and str(exc).startswith("payload"):
            raise
        raise ValueError("payload must contain valid JSON-compatible data") from exc


def _check_schema(
    payload: dict[str, Any],
    fields: tuple[EventField, ...],
    maximum_payload_bytes: int,
    allow_unknown_fields: bool,
    record_name: str,
) -> None:
    size = _payload_size(payload)
    by_name = {item.name: item for item in fields}
    missing = [item.name for item in fields if item.required and item.name not in payload]
    if missing:
        raise ValueError(f"{record_name} missing required fields: {', '.join(missing)}")
    unknown = set(payload) - set(by_name)
    if unknown and not allow_unknown_fields:
        raise ValueError(f"{record_name} contains unknown fields: {', '.join(sorted(unknown))}")
    for name, value in payload.items():
        field_spec = by_name.get(name)
        if field_spec is not None and not _matches_type(value, field_spec.value_type):
            kind = record_name.removesuffix(" payload")
            raise ValueError(f"{kind} field {name} must be {field_spec.value_type}")
    if size > maximum_payload_bytes:
        raise ValueError(f"{record_name} exceeds maximum_payload_bytes")


def _validate_timestamp(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_json_object(value: str, expected_fields: set[str], envelope_name: str) -> dict[str, Any]:
    if not isinstance(value, str):
        raise ValueError(f"{envelope_name} must be valid JSON")
    try:
        if len(value.encode("utf-8")) > _MAX_ENVELOPE_BYTES:
            raise ValueError(f"{envelope_name} exceeds the maximum encoded size")
    except UnicodeError as exc:
        raise ValueError(f"{envelope_name} must be valid UTF-8 JSON") from exc

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in pairs:
            if key in result:
                raise ValueError(f"{envelope_name} contains duplicate JSON field: {key}")
            result[key] = item
        return result

    try:
        parsed = json.loads(value, object_pairs_hook=reject_duplicate_keys)
    except (json.JSONDecodeError, RecursionError, TypeError) as exc:
        raise ValueError(f"{envelope_name} must be valid JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{envelope_name} must be a JSON object")
    if set(parsed) != expected_fields:
        raise ValueError(f"{envelope_name} fields do not match the versioned envelope schema")
    return parsed


@dataclass(frozen=True, slots=True)
class EventField:
    name: str
    value_type: str
    required: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not _SAFE_TYPE.fullmatch(self.name):
            raise ValueError("event field name must be a safe identifier")
        if not isinstance(self.value_type, str) or self.value_type not in _FIELD_TYPES:
            raise ValueError(f"unsupported event field type: {self.value_type}")
        if not isinstance(self.required, bool):
            raise ValueError("field required flag must be a boolean")


@dataclass(frozen=True, slots=True)
class EventSchema:
    event_type: str
    version: int
    fields: tuple[EventField, ...]
    maximum_payload_bytes: int = _MAX_PAYLOAD_BYTES
    allow_unknown_fields: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.event_type, str) or not _SAFE_TYPE.fullmatch(self.event_type):
            raise ValueError("event_type must be a safe identifier")
        _positive_version(self.version, "event schema version")
        _validate_schema_options(
            self.fields, self.maximum_payload_bytes, self.allow_unknown_fields, EventField
        )

    def validate_payload(self, payload: dict[str, Any]) -> None:
        _check_schema(
            payload,
            self.fields,
            self.maximum_payload_bytes,
            self.allow_unknown_fields,
            "event payload",
        )

    def validate(self, event: EventEnvelope) -> None:
        if event.event_type != self.event_type:
            raise ValueError("event type does not match schema")
        if event.schema_version != self.version:
            raise ValueError("event version does not match schema")
        self.validate_payload(event.payload)


@dataclass(frozen=True, slots=True)
class MessageField:
    name: str
    value_type: str
    required: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not _SAFE_TYPE.fullmatch(self.name):
            raise ValueError("message field name must be a safe identifier")
        if not isinstance(self.value_type, str) or self.value_type not in _FIELD_TYPES:
            raise ValueError(f"unsupported message field type: {self.value_type}")
        if not isinstance(self.required, bool):
            raise ValueError("field required flag must be a boolean")


@dataclass(frozen=True, slots=True)
class MessageSchema:
    message_type: str
    version: int
    fields: tuple[MessageField, ...]
    maximum_payload_bytes: int = _MAX_PAYLOAD_BYTES
    allow_unknown_fields: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.message_type, str) or not _SAFE_TYPE.fullmatch(self.message_type):
            raise ValueError("message_type must be a safe identifier")
        _positive_version(self.version, "message schema version")
        _validate_schema_options(
            self.fields, self.maximum_payload_bytes, self.allow_unknown_fields, MessageField
        )

    def validate_payload(self, payload: dict[str, Any]) -> None:
        _check_schema(
            payload,
            self.fields,
            self.maximum_payload_bytes,
            self.allow_unknown_fields,
            "message payload",
        )

    def validate(self, message: MessageEnvelope) -> None:
        if message.message_type != self.message_type:
            raise ValueError("message type does not match schema")
        if message.schema_version != self.version:
            raise ValueError("message version does not match schema")
        self.validate_payload(message.payload)


def _validate_schema_options(
    fields: tuple[EventField, ...] | tuple[MessageField, ...],
    maximum_payload_bytes: int,
    allow_unknown_fields: bool,
    field_type: type[EventField] | type[MessageField],
) -> None:
    if not isinstance(fields, tuple) or any(not isinstance(item, field_type) for item in fields):
        raise ValueError("schema fields must be a tuple of field definitions")
    if (
        isinstance(maximum_payload_bytes, bool)
        or not isinstance(maximum_payload_bytes, int)
        or not 1 <= maximum_payload_bytes <= _MAX_PAYLOAD_BYTES
    ):
        raise ValueError("maximum_payload_bytes must be between 1 and 65536")
    if not isinstance(allow_unknown_fields, bool):
        raise ValueError("allow_unknown_fields must be a boolean")
    names = [item.name for item in fields]
    if len(names) != len(set(names)):
        raise ValueError("schema field names must be unique")


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
        if (
            not isinstance(self.event_type, str)
            or not _SAFE_TYPE.fullmatch(self.event_type)
            or not isinstance(self.source, str)
            or not _SAFE_TYPE.fullmatch(self.source)
        ):
            raise ValueError("event_type and source must be safe identifiers")
        _positive_version(self.schema_version, "schema_version")
        object.__setattr__(self, "timestamp_utc", _validate_timestamp(self.timestamp_utc))
        _validate_uuid(self.event_id, "event_id")
        if _payload_size(self.payload) > _MAX_PAYLOAD_BYTES:
            raise ValueError("event payload exceeds 65536 bytes")

    def to_json(self) -> str:
        result = json.dumps(
            {
                "event_id": self.event_id,
                "event_type": self.event_type,
                "payload": self.payload,
                "schema_version": self.schema_version,
                "source": self.source,
                "timestamp_utc": self.timestamp_utc,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        if len(result.encode("utf-8")) > _MAX_ENVELOPE_BYTES:
            raise ValueError("event envelope exceeds the maximum encoded size")
        return result

    @classmethod
    def from_json(cls, value: str) -> EventEnvelope:
        data = _parse_json_object(
            value,
            {"event_id", "event_type", "payload", "schema_version", "source", "timestamp_utc"},
            "event envelope",
        )
        return cls(**data)


@dataclass(frozen=True, slots=True)
class MessageEnvelope:
    """Typed data only; receipt of a message does not confer runtime authority."""

    message_type: str
    payload: dict[str, Any]
    schema_version: int = 1
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.message_type, str) or not _SAFE_TYPE.fullmatch(self.message_type):
            raise ValueError("message_type must be a safe identifier")
        _positive_version(self.schema_version, "schema_version")
        _validate_uuid(self.message_id, "message_id")
        if self.correlation_id is not None:
            _validate_uuid(self.correlation_id, "correlation_id")
        if _payload_size(self.payload) > _MAX_PAYLOAD_BYTES:
            raise ValueError("message payload exceeds 65536 bytes")

    def to_json(self) -> str:
        result = json.dumps(
            {
                "correlation_id": self.correlation_id,
                "message_id": self.message_id,
                "message_type": self.message_type,
                "payload": self.payload,
                "schema_version": self.schema_version,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        if len(result.encode("utf-8")) > _MAX_ENVELOPE_BYTES:
            raise ValueError("message envelope exceeds the maximum encoded size")
        return result

    @classmethod
    def from_json(cls, value: str) -> MessageEnvelope:
        data = _parse_json_object(
            value,
            {"correlation_id", "message_id", "message_type", "payload", "schema_version"},
            "message envelope",
        )
        return cls(**data)


def _validate_uuid(value: str, field_name: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a UUID")
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"{field_name} must be a UUID") from exc
