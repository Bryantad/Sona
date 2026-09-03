# Proof Capabilities and Effects

Schema-1 capability records are explicit booleans:

- `console`
- `filesystem_read`
- `filesystem_write`
- `network`
- `process`
- `environment`

Without Guardian, these booleans record the Native Core grants selected by the
documented CLI flags. With a policy-aware `--guardian-root`, filesystem and
network flags are requests: the recorded grant is true only when both the flag
was requested and the trusted Guardian policy says `allow`. Console remains
available; process and environment remain unavailable in this foundation.

Effect records are ordered observations of host-facing operations during Native
Core execution. Each effect contains:

- `sequence`: contiguous integer starting at `1`
- `scope`: non-empty low-level scope string
- `operation`: non-empty low-level operation string
- `outcome`: one of `allowed`, `denied`, `failed`, or `unavailable`
- `target`: optional `hmac-sha256:<64 hex chars>` fingerprint

Current producers add two paired fields for registered operations:

- `effect`: stable normalized identifier for tools and terminal output
- `support`: observation-support status for that identifier

The low-level `scope` and `operation` remain authoritative evidence. The
normalized fields do not hide or replace them.

## Outcomes and support are different

`outcome` describes what happened during this attempt:

- `allowed`: the observed operation completed through the instrumented host
  boundary
- `denied`: a capability decision blocked the attempt
- `failed`: the attempt reached the boundary but failed for another reason
- `unavailable`: capability policy allowed the attempt, but Native Core does
  not currently implement the operation

`support` describes the observation contract:

- `SUPPORTED`: Native Core has a direct instrumented boundary for the event
- `PARTIAL`: the boundary is observed, but the normalized category does not
  describe every related sub-effect or byte source
- `UNOBSERVED`: the vocabulary names a useful boundary that Native Core does
  not independently instrument; no occurrence may be inferred
- `UNAVAILABLE`: the attempted operation is observed, but the runtime feature
  cannot currently complete

## Registered vocabulary

| Normalized effect | Low-level operations | Support | Notes |
| --- | --- | --- | --- |
| `FS.READ` | `fs.read_text`, `fs.copy.source` | `SUPPORTED` | Target path is an execution-local HMAC fingerprint |
| `FS.READ` | `fs.exists`, `fs.is_file`, `fs.is_dir` | `PARTIAL` | Records metadata predicates rather than content reads |
| `FS.WRITE` | `fs.write_text`, `fs.copy.destination` | `PARTIAL` | A write may also create, truncate, or replace a file |
| `FS.APPEND` | `fs.append_text` | `SUPPORTED` | Target is fingerprinted |
| `FS.CREATE` | `fs.create_dir` | `SUPPORTED` | Target is fingerprinted |
| `FS.DELETE` | `fs.remove` | `SUPPORTED` | Target is fingerprinted |
| `FS.RENAME` | `fs.rename.source`, `fs.rename.destination` | `SUPPORTED` | One rename produces two ordered target records |
| `FS.LIST` | `fs.list_dir` | `SUPPORTED` | Target is fingerprinted; entries are omitted |
| `STDIN.READ` | `stdin.read` | `SUPPORTED` | Prompt and input values are omitted |
| `STDOUT.WRITE` | `print`, `io.write_stdout` | `PARTIAL` | Aggregate stdout evidence can cover bytes beyond semantic effect records |
| `STDERR.WRITE` | `io.write_stderr` | `PARTIAL` | Aggregate stderr evidence can cover bytes beyond semantic effect records |
| `CONSOLE.FLUSH` | `io.flush` | `PARTIAL` | Records the flush boundary, not operating-system durability |
| `NET.REQUEST` | `http.get`, `http.post`, `http.put`, `http.patch`, `http.delete` | `UNAVAILABLE` | Attempts are observed; Native HTTP returns `SONA-HTTP-005` |
| `CLOCK.READ` | `date.today`, `time.now`, `time.timestamp`, `time.monotonic` | `SUPPORTED` | Returned time values are omitted |
| `CLOCK.SLEEP` | `time.sleep` | `SUPPORTED` | Requested duration is omitted |
| `RANDOM.READ` | `random.float`, `random.integer`, `random.choice`, `random.shuffle` | `SUPPORTED` | Arguments and returned values are omitted |
| `RANDOM.SEED` | `random.seed` | `SUPPORTED` | Seed value is omitted |

`NET.CONNECT` is registered only as `UNOBSERVED`: Native Core has no
independently instrumented connection boundary. It is not emitted or inferred
from `NET.REQUEST`.

The machine-readable contract is
`tests/proof/vectors/effect-vocabulary.json`. Rust producer tests and Python
verifier tests consume the same file.

Targets are redacted fingerprints. Receipts must not store raw paths, raw URLs,
stdin values, random seeds or results, clock values, stdout/stderr bodies,
source text, or environment values.

Effect records describe only the instrumented Native host boundaries that ran.
An absent effect does not prove that the broader operating system, parent
process, or uninstrumented code performed no such activity.

`AGENT.ACTION` is not registered. It is currently application-level metadata,
not a Native runtime observation. See
[Proof Mode and Trusted Automation](automation.md) for the decision and future
requirements.
