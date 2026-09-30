"""Typed, synchronous publish/subscribe dispatch for validated event envelopes."""

from __future__ import annotations

import re
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass

from .events import EventEnvelope, EventSchema

_SAFE_SUBSCRIPTION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
EventHandler = Callable[[EventEnvelope], None]


class EventBusError(RuntimeError):
    """Base error for event-bus lifecycle and delivery failures."""


class EventBusClosedError(EventBusError):
    """Raised when an operation is attempted after the bus closes."""


class EventSchemaNotRegistered(EventBusError):
    """Raised when an event type/version has no registered schema."""


class EventBusFullError(EventBusError):
    """Raised when the configured subscription bound has been reached."""


class EventDeliveryError(EventBusError):
    """Reports failed subscribers without retaining or exposing handler exceptions."""

    def __init__(
        self,
        event_id: str,
        *,
        subscriber_count: int,
        delivered_count: int,
        failed_subscription_ids: tuple[str, ...],
    ) -> None:
        self.event_id = event_id
        self.subscriber_count = subscriber_count
        self.delivered_count = delivered_count
        self.failed_subscription_ids = failed_subscription_ids
        super().__init__(
            f"event {event_id} delivery failed for {len(failed_subscription_ids)} "
            f"of {subscriber_count} subscribers"
        )


@dataclass(frozen=True, slots=True)
class EventSubscription:
    subscription_id: str
    event_type: str
    schema_version: int


@dataclass(frozen=True, slots=True)
class EventDeliveryReceipt:
    event_id: str
    subscriber_count: int
    delivered_count: int


@dataclass(frozen=True, slots=True)
class _Subscriber:
    subscription: EventSubscription
    handler: EventHandler


class EventBus:
    """Synchronous typed event fan-out; use bounded channels for buffered delivery.

    Subscribers run on the publisher's thread in registration order. A slow
    subscriber therefore blocks that publish call instead of building an
    unbounded queue. Each subscriber receives its own decoded envelope copy so
    it cannot mutate the event seen by another subscriber.
    """

    def __init__(
        self,
        *,
        maximum_subscribers: int = 1024,
        maximum_schemas: int = 4096,
    ) -> None:
        _validate_bound(maximum_subscribers, "maximum_subscribers")
        _validate_bound(maximum_schemas, "maximum_schemas")
        self._lock = threading.RLock()
        self._schemas: dict[tuple[str, int], EventSchema] = {}
        self._subscribers: dict[str, _Subscriber] = {}
        self._closed = False
        self._maximum_subscribers = maximum_subscribers
        self._maximum_schemas = maximum_schemas

    @property
    def closed(self) -> bool:
        with self._lock:
            return self._closed

    def register_schema(self, schema: EventSchema) -> None:
        if not isinstance(schema, EventSchema):
            raise TypeError("schema must be an EventSchema")
        key = (schema.event_type, schema.version)
        with self._lock:
            self._ensure_open()
            if key in self._schemas:
                raise EventBusError(
                    "an event schema with this type and version is already registered"
                )
            if len(self._schemas) >= self._maximum_schemas:
                raise EventBusFullError("event bus schema limit reached")
            self._schemas[key] = schema

    def subscribe(
        self,
        event_type: str,
        schema_version: int,
        handler: EventHandler,
        *,
        subscription_id: str | None = None,
    ) -> EventSubscription:
        if not callable(handler):
            raise TypeError("event handler must be callable")
        if not isinstance(event_type, str) or not event_type:
            raise ValueError("event_type must be a non-empty string")
        if (
            isinstance(schema_version, bool)
            or not isinstance(schema_version, int)
            or schema_version <= 0
        ):
            raise ValueError("schema_version must be a positive integer")
        resolved_id = str(uuid.uuid4()) if subscription_id is None else subscription_id
        if not isinstance(resolved_id, str) or not _SAFE_SUBSCRIPTION_ID.fullmatch(resolved_id):
            raise ValueError("subscription_id must be a safe identifier")
        subscription = EventSubscription(resolved_id, event_type, schema_version)
        with self._lock:
            self._ensure_open()
            if (event_type, schema_version) not in self._schemas:
                raise EventSchemaNotRegistered("register the exact event schema before subscribing")
            if resolved_id in self._subscribers:
                raise EventBusError("subscription_id is already registered")
            if len(self._subscribers) >= self._maximum_subscribers:
                raise EventBusFullError("event bus subscriber limit reached")
            self._subscribers[resolved_id] = _Subscriber(subscription, handler)
        return subscription

    def unsubscribe(self, subscription: EventSubscription | str) -> bool:
        if isinstance(subscription, EventSubscription):
            subscription_id = subscription.subscription_id
        elif isinstance(subscription, str):
            subscription_id = subscription
        else:
            raise TypeError("subscription must be an EventSubscription or ID")
        with self._lock:
            self._ensure_open()
            return self._subscribers.pop(subscription_id, None) is not None

    def publish(self, event: EventEnvelope) -> EventDeliveryReceipt:
        if not isinstance(event, EventEnvelope):
            raise TypeError("event must be an EventEnvelope")
        encoded = event.to_json()
        snapshot = EventEnvelope.from_json(encoded)
        with self._lock:
            self._ensure_open()
            schema = self._schemas.get((snapshot.event_type, snapshot.schema_version))
            if schema is None:
                raise EventSchemaNotRegistered(
                    "no schema is registered for this event type/version"
                )
            schema.validate(snapshot)
            subscribers = tuple(
                subscriber
                for subscriber in self._subscribers.values()
                if subscriber.subscription.event_type == snapshot.event_type
                and subscriber.subscription.schema_version == snapshot.schema_version
            )

        failed: list[str] = []
        for subscriber in subscribers:
            delivery = EventEnvelope.from_json(encoded)
            try:
                subscriber.handler(delivery)
            except Exception:
                failed.append(subscriber.subscription.subscription_id)
        delivered = len(subscribers) - len(failed)
        if failed:
            raise EventDeliveryError(
                snapshot.event_id,
                subscriber_count=len(subscribers),
                delivered_count=delivered,
                failed_subscription_ids=tuple(failed),
            )
        return EventDeliveryReceipt(snapshot.event_id, len(subscribers), delivered)

    def close(self) -> bool:
        with self._lock:
            if self._closed:
                return False
            self._closed = True
            self._subscribers.clear()
            self._schemas.clear()
            return True

    def _ensure_open(self) -> None:
        if self._closed:
            raise EventBusClosedError("event bus is closed")


def _validate_bound(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 65_536:
        raise ValueError(f"{name} must be between 1 and 65536")
