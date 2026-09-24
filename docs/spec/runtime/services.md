# Supervised Services (0.16.0 foundation)

## Scope

`ServiceSupervisor` manages synchronous, in-process service callables on
dedicated threads. A service target receives `ServiceContext`, performs its
startup, calls `mark_healthy()` when it is ready, then continues until it
returns or observes cooperative cancellation with `wait_cancelled()`.

This is a process-local supervision API, not an OS process manager, sandbox,
durable service registry, distributed supervisor, or automatic restart after
host failure. It does not grant capabilities, enforce `ResourceBudget`, or
make service health an authorization decision. Service targets should route
effects through separately governed APIs.

## Registration and tree

Register a `ServiceDefinition` and a synchronous target accepting one context
argument. Optional `parent_service_id` forms an explicit tree. Parents must be
registered before children; a child can start only while its parent is
`HEALTHY`. Starting a parent does not automatically start children. A parent
failure does not automatically stop or restart children or any other service;
each service has an independent lifecycle. `stop(..., cascade=True)` provides
an explicit child-first subtree shutdown.

Duplicate/unknown IDs, invalid targets, duplicate registrations, invalid
state operations, and child starts before parent health fail without silently
changing other services.

## Lifecycle and readiness

Initial state is `STOPPED`. `start()` changes it to `STARTING` and starts the
target. Only an explicit `context.mark_healthy()` changes state to `HEALTHY`;
this is the service's own readiness report, not an external health probe. A
service that returns normally becomes `STOPPED` and is not restarted. A
service target is cooperative: `stop()` requests cancellation but does not
force-kill its thread. If it does not stop before the requested timeout,
`stop()` returns `False` and its state remains `STOPPING` until the target
actually exits.

Snapshots report service ID, parent ID, lifecycle state, attempt count,
restart count, safe failure code, UTC update time, and a separate health
snapshot. The health subject uses its own `HealthPolicy`; see
[`health-state-machines.md`](health-state-machines.md). `mark_healthy()` is
both the startup-ready transition and an explicit HEALTHY report. Later,
`context.heartbeat()` refreshes liveness, while `context.report_health()` can
report DEGRADED/UNHEALTHY/UNKNOWN independently of service lifecycle. A
stopped, stopping, or failed service is exposed with health UNKNOWN. Health
does not itself trigger restarts or authorize operations. Exception messages
and tracebacks are not retained in snapshots. `wait_for_state()` requires a
finite timeout.

## Bounded restart policy

`RestartPolicy` allows at most 1,000 restarts and a finite delay from zero to
one day. `NEVER` does not restart. `ON_FAILURE` and `BOUNDED` both restart
failed targets up to the explicitly configured finite maximum; `BOUNDED` makes
that cap explicit in configuration. A delay waits cooperatively, so stop
cancels a pending restart immediately. After budget exhaustion, the service
becomes `FAILED` with `SONA-SERVICE-FAILED`; raw exception text is excluded.
Starting a terminally failed service again is an explicit owner action and
starts a fresh attempt budget.

Each service owns its restart loop. A failure or exhausted budget in one
service does not terminate unrelated service threads. No restart storm can
exceed that service's configured cap.

## Example

```python
from sona.runtime import (
    RestartMode,
    RestartPolicy,
    ServiceDefinition,
    ServiceSupervisor,
)

def worker(context):
    context.mark_healthy()
    while not context.wait_cancelled(timeout=0.5):
        do_one_bounded_unit_of_work()

supervisor = ServiceSupervisor()
supervisor.register(
    ServiceDefinition(
        "indexer",
        restart_policy=RestartPolicy(
            RestartMode.BOUNDED,
            maximum_restarts=3,
            delay_seconds=1.0,
        ),
    ),
    worker,
)
supervisor.start("indexer")
# Owner later calls supervisor.close(timeout=5.0).
```

No Sona service syntax, health-driven restart, resource enforcement,
persistence, or proof binding is introduced here. Those remain later phases
and must reuse Guardian/Proof boundaries without weakening them.
