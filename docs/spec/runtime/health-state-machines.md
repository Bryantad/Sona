# Health, Heartbeats, and State Machines (0.16.0 foundation)

## Health and heartbeats

`HealthMonitor` tracks explicitly reported health separately from service
lifecycle and authorization. A subject starts `UNKNOWN`. `report(id, state)`
sets one of `HEALTHY`, `DEGRADED`, `UNHEALTHY`, or `UNKNOWN`; optional
diagnostics must be safe uppercase codes and are never raw exception/OS text.

`heartbeat(id)` records fresh contact, increments heartbeat count and sequence,
but does not promote an `UNKNOWN` subject or clear an explicitly reported
`DEGRADED`/`UNHEALTHY` state. Default thresholds derive `DEGRADED` after 10
seconds and `UNHEALTHY` after 30 seconds without a new heartbeat or health
report. A fresh heartbeat clears only this staleness-derived state and restores
the last explicit report. Thresholds are configurable, finite, ordered, and
capped at 30 days.

Health is evaluated when a snapshot is read; there is no timer thread. The
monitor uses monotonic elapsed time and separately records UTC observation
time. It reports state, sequence, heartbeat count, observation age, and safe
diagnostic code. This is advisory lifecycle data: health never grants a
capability, proves an effect, or makes a Guardian decision. No automatic
restart occurs merely because a health report is degraded or unhealthy.

`ServiceSupervisor` includes health in each `ServiceSnapshot`. A service
reports initial readiness through `ServiceContext.mark_healthy()`. It can then
call `heartbeat()` to refresh contact and `report_health()` to explicitly
change its health. Service lifecycle can remain `HEALTHY` while health becomes
`DEGRADED` or `UNHEALTHY`; these are separate dimensions. A stopped, stopping,
or failed service is exposed with health `UNKNOWN`.

## Generic finite state machines

`StateMachineDefinition` declares a unique tuple of states, initial state, and
explicit `StateTransition(from_state, event, to_state)` records. State/event
names use the safe identifier form
`[A-Za-z][A-Za-z0-9_.-]{0,127}`. Definitions reject undeclared states,
duplicate `(from_state, event)` pairs, and limits above 4,096 states or 65,536
transitions.

`StateMachine.trigger(event)` atomically applies only a declared transition.
An invalid event raises `InvalidStateTransition` and leaves the state,
sequence, and last-event evidence unchanged. Successful transitions increment
sequence by one. `can_trigger()` is a read-only query. These records do not run
callbacks or effects and are not yet wired into workflow or service lifecycle
execution.

## Example

```python
from sona.runtime import StateMachine, StateMachineDefinition, StateTransition

machine = StateMachine(
    StateMachineDefinition(
        states=("closed", "opening", "open"),
        initial_state="closed",
        transitions=(
            StateTransition("closed", "open_requested", "opening"),
            StateTransition("opening", "opened", "open"),
        ),
    )
)
machine.trigger("open_requested")
machine.trigger("opened")
```

## Limitations

- Health and state-machine data are process-local and not journaled.
- Heartbeat checks are snapshot-driven, not background monitoring.
- There is no automatic service restart based on health; bounded restarts
  remain tied to service target failure.
- Health status is not permission, trusted identity, Proof evidence, or an
  assertion that every external dependency is healthy.
- Generic state machines do not yet drive workflow, service, protocol, or UI
  transitions.
