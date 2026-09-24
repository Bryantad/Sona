# Workflow Ledger (0.16.0 foundation)

## Scope

`sona.workflow.WorkflowLedger` validates lifecycle transitions and progress.
Without a store it is process-local. When constructed with
`WorkflowJournalStore(root)`, every accepted mutation is journaled before the
new state is returned. Neither mode invokes the `operation` string in a
`StepDefinition` or launches processes; an external owner reports step
completion, failure, blocking, and cancellation.

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
clock values are rejected; timestamps are normalized to UTC. The ledger
accepts one active step per workflow. `restore()` explicitly reads persisted
state but never executes a step. A step last recorded as `RUNNING` or
`CANCELING` is conservatively restored as `BLOCKED` with
`SONA-WORKFLOW-RECOVERY-REQUIRED`; the owner must make a separate recovery
decision. IDs, dependencies, retry policy, attempt counts, timestamps,
terminal state, and safe failure codes survive reopen. Retry policy is stored,
but automatic retry/backoff and policy-bound approval records remain future
work.

## Durable format and publication

Each workflow has an append-only directory under the caller-selected store
root. `event-00000001.json`, etc., are canonical UTF-8 JSON records containing
the schema version, event identity/type, sequence, complete version-1 state
snapshot, previous record hash, and current SHA-256 hash. A staged file is
flushed before it is atomically published without replacing an existing event.
The `snapshot.json` file is a replaceable cache; the journal is authoritative
and a missing/stale cache is rebuilt from validated records. A partial/corrupt
event, noncanonical JSON, sequence gap, invalid state snapshot, or broken hash
chain fails closed rather than silently truncating history. Data is bounded by
configurable workflow-count, event-count, record-size, and aggregate-byte
limits. Publication is serialized among store objects in one process; callers
must use a single writer per root across processes.
Temporary files and directories with no published event are treated as
uncommitted work and ignored on reopen; a published event is the commit point.

Persisted workflow operation names must be registered-style identifiers
(`A-Za-z` followed by at most 127 letters, digits, `_`, `.`, `:`, or `-`).
Arbitrary command text, paths, prompts, and environment values are not valid
durable operation identifiers. The journal is local integrity evidence, not a
signature or protection against an actor who can rewrite the journal and
recompute its hashes. Directory-entry fsync is best-effort on Windows.

## Trust and effects boundary

The ledger does not persist execution approval, authorize capabilities,
perform effects, generate proof receipts, or make Guardian decisions. Future
orchestration must separately connect policy decisions, capability grants,
the native execution boundary, effect capture, and proof receipts. Workflow
status alone is not evidence that an operation ran or that a reported result
is trustworthy.

## Tests

The focused contract tests cover dependency ordering (including cross-task
dependencies), progress, transitions, safe failure codes, blocking and
unblocking, cancellation acknowledgment, duplicate and unknown identities,
timezone-aware clocks, inert restore, recovery-required conversion, journal
limits, atomic cache rebuilding, hash-chain/canonical validation, persistence
failure rollback, and the guarantee that an operation string is inert.
