# Bounded Channels (0.16.0 foundation)

## Scope and authority

`sona.runtime.BoundedChannel` is an in-process, thread-safe FIFO for validated
`MessageEnvelope` data. A `ChannelDefinition` fixes a safe channel identity,
message type, capacity (1–65,536), and explicit `BLOCK`, `REJECT`, or
`DROP_OLDEST` policy. A matching `MessageSchema` validates every outgoing
message before it can enter the queue.

Messages remain data, not authority. Channel delivery does not grant
capabilities, authorize effects, establish Guardian policy, or create Proof
evidence. The channel is not durable, cross-process, or a publish/subscribe
event bus. It does not provide persistence, replay, delivery acknowledgement,
or waiter fairness guarantees.

## Send and backpressure

`send(message, timeout=None, cancel_event=None)` snapshots an envelope through
its JSON representation before queueing it, preventing caller mutation while
a sender is blocked. It then checks message type and schema.

- `BLOCK` waits for capacity. A finite timeout raises `ChannelTimeoutError`;
  cancellation raises `ChannelCancelledError`; close wakes the sender and
  raises `ChannelClosedError`. With no timeout/cancellation it may wait until
  a receiver frees capacity or the channel closes.
- `REJECT` raises `ChannelFullError` immediately if full. It never silently
  drops an item.
- `DROP_OLDEST` removes exactly one oldest queued item and accepts the new
  message. `SendReceipt.dropped_message_id` reports the removed message ID.
  This policy is explicitly lossy and should be selected only when appropriate.

An accepted `SendReceipt` has `accepted=True`. Timeouts constrain blocking
operations; they do not interrupt a send that can be accepted immediately.
The channel has a fixed item capacity and never grows its queue beyond it.

## Receive and close

`receive(timeout=None, cancel_event=None)` returns the oldest message. An empty
open channel waits; a timeout raises `ChannelTimeoutError`, and cancellation
raises `ChannelCancelledError`. If the channel is closed, already queued
messages are still drained in FIFO order; after the queue is empty, receive
returns `None` as end-of-stream. Cancellation is checked before removing a
queued item, so a canceled receive does not consume it.

`close()` is idempotent. It returns `True` only for the call that transitions
OPEN to CLOSED, wakes all waiters, rejects future sends, and preserves queued
messages for draining. Closing does not revoke or cancel already accepted data.

The optional `threading.Event` cancellation token is observed while waiting by
bounded polling (at most 50 ms between checks absent scheduler delay). Setting
the event does not close the channel or cancel other callers. Operations are
linearized under the channel lock: a cancellation arriving after an operation
commits does not undo that operation.

## Example

```python
from sona.runtime import (
    BackpressurePolicy,
    BoundedChannel,
    ChannelDefinition,
    MessageEnvelope,
    MessageField,
    MessageSchema,
)

schema = MessageSchema("BuildResult", 1, (MessageField("artifact", "string"),))
results = BoundedChannel(
    ChannelDefinition("build-results", "BuildResult", capacity=32,
                      backpressure=BackpressurePolicy.BLOCK),
    schema,
)
results.send(MessageEnvelope("BuildResult", {"artifact": "sona.exe"}))
result = results.receive(timeout=1.0)
results.close()
```

No Sona language syntax is added in this phase. The Python API is an
experimental runtime foundation and does not define structured-concurrency or
parent/child task behavior.

## Error behavior

- Invalid definitions, timeouts, or cancellation-token types fail before
  blocking.
- A message with the wrong type or schema fails before enqueue.
- A closed channel rejects senders with `ChannelClosedError`.
- Full-channel and timeout cases have distinct exception types.
- Invalid operations do not silently discard queued data, except the explicit
  `DROP_OLDEST` policy.
