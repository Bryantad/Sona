"""Typed synchronous event publication, subscription, and trust semantics."""

from __future__ import annotations

import pytest

from sona.runtime import (
    EventBus,
    EventBusClosedError,
    EventBusError,
    EventBusFullError,
    EventDeliveryError,
    EventEnvelope,
    EventField,
    EventSchema,
    EventSchemaNotRegistered,
)


def _schema(version: int = 1) -> EventSchema:
    return EventSchema("build.completed", version, (EventField("artifact", "string"),))


def _event(version: int = 1, artifact: str = "sona.exe") -> EventEnvelope:
    return EventEnvelope(
        event_type="build.completed",
        source="builder",
        payload={"artifact": artifact},
        schema_version=version,
        timestamp_utc="2026-09-24T12:00:00Z",
    )


def test_bus_validates_and_fans_out_in_registration_order_with_isolated_payloads():
    bus = EventBus()
    bus.register_schema(_schema())
    observed: list[tuple[str, str]] = []

    def first(event: EventEnvelope) -> None:
        observed.append(("first", event.payload["artifact"]))
        event.payload["artifact"] = "mutated.exe"

    def second(event: EventEnvelope) -> None:
        observed.append(("second", event.payload["artifact"]))

    bus.subscribe("build.completed", 1, first, subscription_id="first")
    bus.subscribe("build.completed", 1, second, subscription_id="second")
    event = _event()

    receipt = bus.publish(event)

    assert observed == [("first", "sona.exe"), ("second", "sona.exe")]
    assert receipt.event_id == event.event_id
    assert receipt.subscriber_count == receipt.delivered_count == 2
    assert event.payload == {"artifact": "sona.exe"}


def test_bus_routes_only_exact_registered_schema_versions_and_requires_schema():
    bus = EventBus()
    bus.register_schema(_schema(1))
    bus.register_schema(_schema(2))
    seen: list[int] = []
    bus.subscribe("build.completed", 1, lambda event: seen.append(event.schema_version))
    bus.subscribe("build.completed", 2, lambda event: seen.append(event.schema_version))

    first = bus.publish(_event(1))
    second = bus.publish(_event(2))

    assert seen == [1, 2]
    assert first.delivered_count == second.delivered_count == 1
    with pytest.raises(EventSchemaNotRegistered, match="type/version"):
        bus.publish(_event(3))


def test_invalid_payload_fails_before_any_subscriber_is_invoked():
    bus = EventBus()
    bus.register_schema(_schema())
    calls: list[str] = []
    bus.subscribe("build.completed", 1, lambda event: calls.append("called"))
    invalid = EventEnvelope(
        "build.completed",
        "builder",
        {},
        1,
        "2026-09-24T12:00:00Z",
    )

    with pytest.raises(ValueError, match="missing required fields"):
        bus.publish(invalid)
    assert calls == []


def test_handler_failures_are_aggregated_without_exception_text_and_other_handlers_run():
    bus = EventBus()
    bus.register_schema(_schema())

    def fail(_event: EventEnvelope) -> None:
        raise RuntimeError("secret token")

    bus.subscribe("build.completed", 1, fail, subscription_id="broken")
    received: list[str] = []
    bus.subscribe("build.completed", 1, lambda event: received.append(event.payload["artifact"]))

    with pytest.raises(EventDeliveryError) as captured:
        bus.publish(_event())

    assert received == ["sona.exe"]
    assert captured.value.failed_subscription_ids == ("broken",)
    assert captured.value.delivered_count == 1
    assert "secret token" not in str(captured.value)


def test_bus_rejects_duplicate_registration_and_closes_idempotently():
    bus = EventBus()
    schema = _schema()
    bus.register_schema(schema)
    with pytest.raises(EventBusError, match="already registered"):
        bus.register_schema(schema)
    bus.subscribe("build.completed", 1, lambda event: None, subscription_id="consumer")
    with pytest.raises(EventBusError, match="already registered"):
        bus.subscribe("build.completed", 1, lambda event: None, subscription_id="consumer")

    assert bus.close() is True
    assert bus.close() is False
    assert bus.closed is True
    with pytest.raises(EventBusClosedError, match="closed"):
        bus.publish(_event())


def test_bus_bounds_subscribers_and_unsubscribe_removes_future_delivery():
    bus = EventBus(maximum_subscribers=1)
    bus.register_schema(_schema())
    calls: list[str] = []
    subscription = bus.subscribe(
        "build.completed", 1, lambda event: calls.append(event.event_id), subscription_id="only"
    )
    with pytest.raises(EventBusFullError, match="limit reached"):
        bus.subscribe("build.completed", 1, lambda event: None, subscription_id="overflow")

    assert bus.unsubscribe(subscription) is True
    assert bus.unsubscribe(subscription.subscription_id) is False
    assert bus.publish(_event()).delivered_count == 0
    assert calls == []


def test_bus_bounds_registered_schemas():
    bus = EventBus(maximum_schemas=1)
    bus.register_schema(_schema(1))
    with pytest.raises(EventBusFullError, match="schema limit reached"):
        bus.register_schema(_schema(2))


@pytest.mark.parametrize("maximum", [0, -1, True, 65_537, 1.5])
def test_event_bus_rejects_invalid_subscriber_bounds(maximum):
    with pytest.raises(ValueError, match="maximum_subscribers"):
        EventBus(maximum_subscribers=maximum)


@pytest.mark.parametrize("maximum", [0, -1, True, 65_537, 1.5])
def test_event_bus_rejects_invalid_schema_bounds(maximum):
    with pytest.raises(ValueError, match="maximum_schemas"):
        EventBus(maximum_schemas=maximum)
