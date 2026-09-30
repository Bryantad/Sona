# Typed Events and Messages (0.16.0 foundation)

## Scope

`sona.runtime.events` defines versioned event and message schemas, validated
envelopes, and a JSON transport representation. `sona.runtime.EventBus` adds
typed synchronous publish/subscribe dispatch. This remains an in-process API,
not a durable event journal, distributed bus, scheduler, or workflow executor.

Receiving or constructing an event/message never grants a capability, approves
an operation, proves that an effect occurred, or authorizes execution. These
records carry data only. Policy and capability decisions remain separate.

## Schemas

`EventSchema` and `MessageSchema` identify a type and positive integer version,
declare a tuple of `EventField` or `MessageField` records, and set a payload
limit from 1 through 65,536 bytes. Field names use the safe identifier format
`[A-Za-z][A-Za-z0-9_.-]{0,127}`. Supported field types are `string`,
`integer`, `number`, `boolean`, `object`, `array`, and `null`.

Required fields must be present, values must match their declared type, and
unknown fields are rejected by default. `allow_unknown_fields=True` is an
explicit compatibility choice; it does not waive validation of declared
fields or the payload size limit. Integer fields do not accept booleans, even
though Python models booleans as integers. Nested payload data must consist
only of JSON values, use string object keys, and contain finite numbers.

Schema versions are exact matches. A producer or consumer must deliberately
select the matching schema version; these contracts do not guess migrations.

## Envelopes

An `EventEnvelope` contains `event_type`, `event_id` (UUID), `source`,
`timestamp_utc`, `schema_version`, and an object `payload`. IDs default to a
random UUID. Timestamps must include a timezone and are normalized to UTC `Z`
form. `EventSchema.validate(envelope)` checks type, version, fields, and size.

A `MessageEnvelope` contains `message_type`, `message_id` (UUID), optional
UUID `correlation_id`, `schema_version`, and an object `payload`.
`MessageSchema.validate(envelope)` checks type, version, fields, and size.
Correlation IDs are identifiers only; they are not workflow identity or trust
evidence.

Both envelope kinds are limited to 65,536 UTF-8 bytes for their canonical
payload JSON. Their encoded JSON envelopes are separately capped at 67,584
bytes before decoding, bounding parser input as well as payload data.
`to_json()` emits compact JSON with sorted envelope keys.
`from_json()` requires exactly the known envelope fields, rejects duplicate
top-level JSON keys, and validates the decoded envelope. This representation
is transport-friendly; it does not itself provide authentication, encryption,
durability, or canonical signed bytes.

## Event bus

Register each exact `(event_type, schema_version)` before subscribing. A
subscription names that exact version and has a stable caller-supplied ID or a
generated UUID. `publish(event)` snapshots the event through its validated
JSON representation, validates it against the registered schema, and invokes
matching subscribers in registration order on the publisher's thread. Each
subscriber receives an independent envelope copy so one handler cannot mutate
what another handler sees. Concurrent publisher calls may invoke a handler
concurrently; the bus does not serialize handlers across separate publishes.
The number of schemas and subscriptions is bounded by `maximum_schemas`
(default 4,096) and `maximum_subscribers` (default 1,024), each with a maximum
of 65,536; adding beyond either limit fails with `EventBusFullError`.

Handlers are synchronous, so a slow handler blocks its publish call; this is
the bus's bounded-by-call-stack backpressure behavior and it creates no queue.
Use `BoundedChannel` when consumers need decoupled, bounded buffering and an
explicit `BLOCK`, `REJECT`, or `DROP_OLDEST` policy. Handler exceptions do not
stop fan-out to later subscribers; after fan-out, `EventDeliveryError` reports
failed subscription IDs and counts but omits raw exception text. Delivery is
not transactional: successful handlers may already have acted when this error
is raised. The caller owns retry/idempotency decisions. Unsubscribing or closing
the bus does not interrupt a publish that already captured its subscriber
snapshot.

## Example

```python
from sona.runtime.events import EventEnvelope, EventField, EventSchema

schema = EventSchema(
    "build.completed",
    version=1,
    fields=(EventField("artifact", "string"),),
)
event = EventEnvelope(
    "build.completed",
    source="builder",
    payload={"artifact": "sona.exe"},
    schema_version=1,
    timestamp_utc="2026-09-24T12:00:00Z",
)
schema.validate(event)
wire_data = event.to_json()
```

The event above records a claim/data item. It does not prove the artifact was
built; that requires an independently governed execution/evidence path.

## Boundaries and deferred work

- Event dispatch is synchronous and process-local; there is no event
  persistence, delivery guarantee, deduplication, or replay.
- Bounded channel behavior and explicit buffered backpressure are separate
  runtime primitives; use the event bus for synchronous fan-out.
- `CapabilityScope`, Guardian policy, workflow approval, and Proof receipts are
  not embedded in these payloads as trusted grants.
- The event JSON form is not the Native Proof receipt format and does not
  change Proof schema-1.
