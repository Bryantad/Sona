# Workflow Ledger (0.16.0 foundation)

## Scope

`sona.workflow.WorkflowLedger` is an in-memory state and progress contract. It
does not invoke the `operation` string in a `StepDefinition`, launch processes,
or provide durable recovery. A workflow is created, explicitly prepared, and
then driven by an owner that reports step completion, failure, blocking, or
cancellation. This foundation is intentionally not a workflow execution
engine.

## Lifecycle

- `create` records a schema-1 workflow in `CREATED` state and rejects duplicate
  workflow IDs in the same ledger.
- `prepare` moves dependency-free steps to `READY` and steps with dependencies
  to `BLOCKED`.
- `start_step` claims one ready step per workflow and increments its attempt
  count. It only records the transition; it does not run the operation.
- `succeed_step` marks the active step successful and makes dependent steps
  ready only after all dependencies succeeded.
- `fail_step` terminates the workflow, marks pending steps skipped, and stores
  only a bounded safe failure code, never exception text.
- `block_step` records an external/policy block; `unblock_step` releases it
  only when declared dependencies have succeeded.
- `cancel` marks pending steps canceled. If a step is active, its state becomes
  `CANCELING`; the owner must call `finish_step_cancellation` after the work has
  actually stopped before the workflow becomes terminally canceled.
- `snapshot` reports immutable task/step state, UTC timestamps, terminal
  outcome, and progress. Terminal progress counts succeeded, failed, canceled,
  and skipped steps as complete.

Invalid transitions are rejected without changing authoritative state. Naive
clock values are rejected; timestamps are normalized to UTC. The ledger is
thread-safe within one process, but provides neither cross-process coordination
nor persistence. Retry policy is represented in workflow definitions, while
automatic retries, backoff, deadlines, durable journals, restart recovery,
bounded parallel scheduling, and actual operation execution remain future
work.

## Trust and effects boundary

The ledger does not authorize capabilities, perform effects, generate proof
receipts, or make Guardian decisions. Future orchestration must separately
connect policy decisions, capability grants, the native execution boundary,
effect capture, and proof receipts. Workflow status alone is not evidence that
an operation ran or that a reported result is trustworthy.

## Tests

The focused contract tests cover dependency ordering (including cross-task
dependencies), progress, transitions, safe failure codes, blocking and
unblocking, cancellation acknowledgment, duplicate and unknown identities,
timezone-aware clocks, and the guarantee that an operation string is inert.
