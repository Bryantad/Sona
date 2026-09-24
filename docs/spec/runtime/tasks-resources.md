# Structured Tasks and Resource Reports (0.16.0 Phase 14)

This document specifies the Python runtime APIs in `sona.runtime.tasks` and
`sona.runtime.resources`. They are in-process contracts; they do not add Sona
syntax or OS process isolation.

## Bounded task group

`BoundedTaskGroup` owns a fixed `maximum_workers` executor and accepts at most
`maximum_tasks` queued or running tasks at once. Since submissions are gated
before reaching the executor, its internal work queue cannot grow beyond that
limit. A further independent `maximum_records` cap bounds retained lifecycle
history. Once the history is full, callers must explicitly `forget()` a
terminal record before submitting more work.

Every submitted callable accepts one `TaskContext`. The task gets a stable
group-local identifier and lifecycle snapshot (`queued`, `running`,
`canceling`, `succeeded`, `failed`, `canceled`) with UTC timestamps. Exceptions
remain observable to the handle's `result()` caller, while snapshots expose
only the fixed `SONA-TASK-FAILED` code.

`cancel_task()` requests cooperative cancellation. Queued tasks are canceled
before start when the executor allows it. Running tasks must check
`TaskContext.cancellation_requested`, wait with `wait_cancelled()`, or call
`raise_if_cancelled()`. Sona cannot forcibly stop a running Python thread. If
the callable ignores cancellation, `close(wait_for_tasks=True)` and normal
context-manager exit wait for it; use `wait_for_tasks=False` only when the
caller deliberately accepts a task outliving the group scope.

An exception leaving the task-group context requests cancellation for its
children and joins them before propagating the original exception. A task
which returns normally after cancellation was requested is considered
succeeded: cooperative code decides whether to finish or raise cancellation.
This class is an API for structured ownership, not durable workflow state,
thread sandboxing, scheduler fairness, or guaranteed preemption.

```python
with BoundedTaskGroup(maximum_workers=2, maximum_tasks=8) as tasks:
    parse = tasks.submit(parse_document, task_id="parse-1")
    index = tasks.submit(index_symbols, task_id="index-1")
    parsed = parse.result()
```

The group provides bounded parallelism but does not guarantee the order in
which competing tasks begin. Applications requiring ordering should express
dependencies before submitting or use the workflow ledger.

## Resource limits and measurements

`ResourceLimit` declares one positive numeric threshold and an
`EnforcementStatus`:

- `ENFORCED`: a trusted adapter claims it actively enforces the threshold.
- `OBSERVED`: the threshold is informational; exceeding it is not prevented.
- `UNSUPPORTED`: this platform/adapter cannot provide that limit; amount must
  be zero.

`ResourceBudgetReporter.report()` accepts caller-supplied typed
`ResourceMeasurement` observations and combines them with declared limits.
For enforced/observed limits it reports `exceeds_limit` as a comparison; for
unsupported limits it reports `None`, never a fabricated pass/fail. The
reporter itself neither collects measurements nor enforces limits. A report
with a limit marked `ENFORCED` relies on the adapter/caller that supplied that
declaration; it is not an independent proof that the enforcement mechanism
worked.

No generic memory/CPU/VRAM enforcement is added by this phase. The task-group
worker and pending-task ceilings are enforced by the group itself; they do not
limit the memory, CPU time, or other resources used within each task.

## Limitations

- Task records and task results are in-memory only and disappear with the
  process; use the workflow persistence APIs for durable progress.
- Cancellation is cooperative for running callables; no thread is force-killed.
- Work can outlive the group only when the caller explicitly closes without
  waiting.
- Resource measurements and enforcement labels are supplied by trusted host
  code, not sampled or independently attested by this reporter.
- Neither API changes Proof schema-1, Guardian policy, service lifecycle, or
  OS-level isolation.
