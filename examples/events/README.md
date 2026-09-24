# Example D — Typed events and bounded messages

```powershell
python examples/events/run_events.py
```

The producer validates a versioned `build.completed` event, converts its data
to a versioned `BuildResult` message, and sends it through a four-item
`REJECT`-on-full channel. The consumer validates the received envelope. This
example uses one process and one message; it does not imply a distributed bus.
