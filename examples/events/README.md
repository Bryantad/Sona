# Example D — Typed events and bounded messages

```powershell
python examples/events/run_events.py
```

The producer publishes a versioned `build.completed` event to a synchronous
typed subscriber, converts the observed data to a versioned `BuildResult`
message, and sends it through a four-item `REJECT`-on-full channel. The channel
consumer validates the received envelope. Event handlers run on the publisher
thread; use bounded channels for explicitly buffered delivery. This example
uses one process and one message; it does not imply a distributed bus.
