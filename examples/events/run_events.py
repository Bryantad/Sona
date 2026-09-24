"""Validate a typed event and move its data through a bounded message channel."""

from __future__ import annotations

from datetime import UTC, datetime

from sona.runtime import (
    BackpressurePolicy,
    BoundedChannel,
    ChannelDefinition,
    EventEnvelope,
    EventField,
    EventSchema,
    MessageEnvelope,
    MessageField,
    MessageSchema,
)


def main() -> int:
    event_schema = EventSchema(
        "build.completed",
        version=1,
        fields=(EventField("artifact", "string"),),
    )
    event = EventEnvelope(
        event_type="build.completed",
        source="example.build",
        payload={"artifact": "sona-demo.zip"},
        schema_version=1,
        timestamp_utc=datetime.now(UTC).isoformat(),
    )
    event_schema.validate(event)

    message_schema = MessageSchema(
        "BuildResult",
        version=1,
        fields=(MessageField("artifact", "string"), MessageField("success", "boolean")),
    )
    channel = BoundedChannel(
        ChannelDefinition(
            "build-results",
            "BuildResult",
            capacity=4,
            backpressure=BackpressurePolicy.REJECT,
        ),
        message_schema,
    )
    message = MessageEnvelope(
        "BuildResult",
        {"artifact": event.payload["artifact"], "success": True},
    )
    channel.send(message)
    received = channel.receive(timeout=1)
    channel.close()
    if received is None:
        print("No message received.")
        return 1
    message_schema.validate(received)
    print(f"Received {received.payload['artifact']}: success={received.payload['success']}")
    print("The event and message carry data only; neither grants capability.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
