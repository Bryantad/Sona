# Sona 0.16.0 — Trusted Intelligent Runtime

> Your model. Your workflows. Your rules.

Sona 0.16.0 expands Sona into a general-purpose runtime for local AI, durable
automation, supervised services, typed events, controlled effects, and
recoverable long-running work. Run local models directly, restore workflows
after interruption, supervise failing services, and keep AI-generated actions
behind validation and explicit approval—all while preserving Sona's existing
Proof Mode and Guardian boundaries.

This release brings together local models, durable workflows, supervised
services, typed concurrency, and trusted effects. The detailed technical and
certification status follows below.

These notes describe the **0.16.0 release candidate**, not a certified final
release. Version alignment and Windows-local test gates have passed, including
the controlled OS-network-off, Ollama-stopped, direct-GGUF run, the full Python
suite, Native Core checks, examples, and local package validation. A complete
integrated acceptance run, hosted Linux/macOS/Windows certification, and
default-branch dependency integration remain open. Do not treat this local
candidate as a cross-platform release.

No Sona syntax change is introduced. Proof schema-1 remains compatible, and
existing Proof Mode and Guardian trust boundaries are preserved.

## Highlights

### Local models and persistent inference

The runtime can register, inspect, test, and report the health of models, and
can use a direct GGUF-backed local inference adapter with a resident service
for repeated requests. Registration and readiness are distinct states; the
runtime does not claim a model is loaded merely because it is registered.

The persistent local GGUF registry now has CLI operations for `sona model add`,
`list`, `inspect`, `remove`, and `default`. Registration validates the GGUF
v2/v3 container structure and selected metadata, canonicalizes the path,
records SHA-256, and does not load or execute the model. `inspect` reports
architecture, context, quantization, file size, observed host hardware, and a
static llama.cpp/device preflight; `--format text` provides a terminal summary,
while JSON remains the default. `inspect --verify-hash` detects
post-registration artifact changes; `remove` removes only the registry entry,
not the model file. Existing developer-intelligence provider descriptors remain
available through the legacy model manifest commands.

The preflight blocks known static mismatches before an expensive model load,
but does not certify architecture support inside llama.cpp, available-memory
headroom, successful loading, or performance. A passing preflight is not a
compatibility guarantee; an explicit load on the target host remains required.

The direct adapter is exercised by configured local integration tests. A GGUF
model is not bundled, and actual model execution requires a compatible local
model/runtime setup.

### Durable, recoverable workflows

Workflow lifecycle state can be journaled and restored as inert data. Recovery
is explicit: restore does not silently resume work. Bounded retries,
cancellation, and caller-directed recovery make interruption behavior
inspectable without promising exactly-once execution or automatic replay.
Workflow steps also support durable delays, absolute deadlines and expiration,
and per-attempt timeouts. These are explicit-poll scheduling contracts: a
running owner must cooperate with cancellation, and restore never starts a
timer or resumes work. New snapshots use schema 3; schema-1 and schema-2
snapshots remain readable.

### Typed communication and bounded concurrency

The runtime adds typed events and messages, a bounded-registration synchronous
event bus, bounded channels with explicit backpressure, supervised service
lifecycle management, and health/heartbeat state contracts. Event handlers
run on the publisher's thread; bounded channels provide buffered delivery when
needed. Task groups cap worker and outstanding-task counts and provide
cooperative cancellation. They do not forcibly preempt running Python code or
impose CPU and memory isolation.

### Explicit effects, capabilities, and proposals

New runtime contracts represent effect decisions separately from operation
outcomes, support exact-resource expiring capability tokens, and gate
data-only proposals through validation and explicit approval callbacks.
These are in-process API contracts: they are not an OS sandbox, and they are
not wired into every runtime operation or Guardian policy loading.
The Guide request API now has a read-only deterministic validation endpoint
for complete proposed source; a validated candidate still requires a separate
editor diff, explicit approval, stale-source check, and apply action.
The VS Code Guide now provides that bounded editor flow for selected code:
direct local GGUF/llama.cpp proposal through the language-server-owned
LocalAIService, deterministic whole-candidate syntax validation, diff review,
explicit user approval, and a one-shot `EDITOR.BUFFER_REPLACE` capability
before application to the editor buffer. It requires a trusted workspace, a
registered intact model, and the optional llama.cpp dependency. Guardian is
optional when uninitialized; configured Guardian state must remain trusted
through capability preparation and consumption. The capability binds the
opaque workspace/document identity, document version, selection, and source,
candidate, and replacement hashes. It does not use Ollama or fall back to a
remote provider. It does not save or run the file. Invalid
Sona syntax is rejected, including when the surrounding file already has
syntax errors.

### CLI and VS Code runtime visibility

The CLI adds read-only workflow inspection and runtime/service status surfaces:

```console
sona workflow list
sona workflow inspect <workflow-id>
sona runtime status
sona service status
sona doctor --format json
```

The VS Code extension adds a Sona Runtime view backed by validated runtime
status data. It distinguishes registered models from loaded readiness and
shows persisted workflow facts without resuming work. New executable examples
cover direct GGUF inference, workflow recovery, supervised service restart,
and typed bounded messages.

### Proof Mode, Guardian, and AI boundaries

Proof Mode's schema-1 receipt format is unchanged. The Python runtime capability
contracts do not imply general Guardian enforcement, and this release does not
add a new attestation mechanism. The Guide editor-buffer flow is the only new
Guardian/capability adapter: it records a bounded in-memory grant/check/revoke,
does not make AI a policy authority, and does not add fields to Proof receipts.
AI/local reasoning remains outside Proof verification and capability
authorization; it cannot create or strengthen receipts or make policy
decisions.

## Development-preview validation status

Local checks on the Windows worktree at recorded checkpoints:

- Before the latest structured-output/chat-template correction, Python
  3.12.13 full suite: **1,046 passed, 6 skipped, 2 warnings** in
  377.13s. Three skips require the absent GGUF artifact/digest; three require
  Windows symlink privilege. The warnings are two Lark deprecations plus
  interpreter-exit `nul` `ResourceWarning`s. A focused post-formatting rerun
  covering the touched CLI, GGUF, EventBus, workflow, Guide, LSP, and provider
  tests passed: **75 passed, 2 warnings** in 3.43s.
- After adding the opt-in Guide chat-template/JSON-grammar path, the focused
  runtime, Guide, LSP, direct GGUF integration, and runtime-example tests
  passed: **26 passed** in 29.89s. This is not a replacement for rerunning the
  full suite against the latest source.
- The subsequent full Python 3.12.13 suite ran with the GGUF path, digest, and
  local-model example configured: **1,056 passed, 3 skipped, 2 warnings** in
  395.53s. All three skips require Windows symlink privileges; the
  model-dependent tests ran. Pytest reported two Lark deprecations, followed
  by two interpreter-exit `nul` `ResourceWarning`s.
- After adding the Guide Guardian/capability gate, the full current suite ran
  again without opt-in model fixtures: **1,059 passed, 6 skipped, 2 warnings**
  in 365.04s. Three GGUF-dependent tests skipped because no model path/digest
  was configured; three Windows symlink tests skipped because this process
  lacks the required privilege. The live-model integration result above is an
  earlier configured run, not evidence for the new authorization boundary.
- The updated extension source passed `npm run compile`, `npm run test:guide`,
  `npm run test`, and `npm run test:runtime` on local Node 24.19.0. The Guide
  smoke uses a stubbed LSP authorization response; it is not a live VS Code plus
  Guardian/model acceptance run. Ruff and Black pass for the new authorization
  module and tests, while broader lint on changed legacy files is not clean.
- The latest source also built temporary 0.15.6 wheel and sdist smoke
  artifacts. The wheel installed into an isolated target, imported the new
  Guide/runtime modules, and returned `status: ok` from `sona runtime status`;
  the sdist contains the changed modules. These are validation outputs, not
  0.16.0 release packages.
- Rust formatting, strict Clippy, and locked workspace tests passed; 39 unit
  tests and all doc-test targets passed.
- A clean temporary extension install under Node 20.19.5/npm 10.8.2 installed
  248 packages. Compile and the AI Console, Guide, and Runtime smoke suites
  passed. A branch `npm audit --audit-level=moderate` reported zero
  vulnerabilities.
- Manual durable-workflow example passed interruption, inert reopen, and
  explicit resume to 3/3 steps. The supervised worker restarted once and
  stopped cooperatively; the typed-event example completed.
- Ruff 0.5.7 and Black 24.8.0 pass on the 14 newly added Python files. A
  broader scan of changed legacy files is not clean; no repository-wide lint
  pass is claimed.
- Revalidation after the final one-shot Guide capability boundary: the full
  Python suite passed **1,065 tests, with 6 skipped and 2 warnings** in
  383.71s. The focused Guide authorization/LSP set passed **11 tests**. VS
  Code compile plus Guide, Runtime, and general extension smokes passed under
  Node 24.19.0. Rust formatting, strict Clippy, and locked workspace tests
  passed again (39 unit tests; doc-test targets passed). This remains local
  Windows evidence, not a final release certification.
- Latest C: worktree rerun on Python 3.12.13 with the pinned optional
  llama.cpp binding installed and no model variables set: **1,065 passed, 6
  skipped, 2 warnings** in 345.26s. The three model-fixture tests are covered
  by the separate configured real-GGUF lane; three symlink tests require
  Windows privilege.
  All 13 official Python-manifest examples passed;
  Rust formatting, strict Clippy, and all 39 Rust unit tests/doc-test targets
  passed. Under pinned Node 20.19.5, extension install, compile, and general,
  Guide, and Runtime smokes passed. The four package-install tests passed;
  temporary wheel and sdist installed in isolated targets and imported the new
  runtime modules. `npm audit --audit-level=moderate` found zero
  vulnerabilities. A separate configured direct-GGUF/runtime-example run
  passed **6 tests** in 94.65s. These are local Windows results, not hosted CI.
- Latest full Python rerun with the staged Qwen3 8B Q4_K_M GGUF path, verified
  SHA-256, and `llama-cpp-python==0.3.35` configured: **1,068 passed, 3
  skipped, 2 warnings** in 430.98s. All model-fixture tests ran; only the
  three Windows symlink-privilege tests skipped. Pytest used a fresh isolated
  temp root after its first attempt reached 100% but exited during cleanup of
  a protected entry under the user's global Temp directory. This is local
  Windows evidence, not hosted CI or the live VS Code approval/apply test.

Current local-model follow-up on this worktree used GGUF artifacts already
present in the local Ollama model store; no model was downloaded or modified.
The direct-runtime integration tests passed with Python socket connection
entry points blocked; the direct local-model example also passed via
`local/llama-cpp` and reported no fallback. A real Qwen3 8.2B Q4_K_M Guide LSP
request, with Python socket entry points blocked, returned `print("new");`
through `local/llama-cpp`, and the separate Sona proposal validator returned
`valid`. Structured output uses llama.cpp's model-specific chat handler and a
JSON grammar. This is local runtime evidence, not the controlled OS-offline
acceptance run: Ollama remained running (with no model loaded), and
operating-system networking remained on.

Model quality is not guaranteed by grammar or syntax validation. In the same
Guide smoke, a smaller Nemotron model returned only `new` for a whole-statement
selection; Sona accepted the identifier as syntactically valid. The editor diff
and human approval are therefore essential, and semantic correctness is not
certified by this test.

Phase 16 remains **PARTIAL / BLOCKED** and the final release is **NOT
CERTIFIED**. Current local certification evidence:

- Python: fresh full run `1066 passed, 6 skipped, 2 warnings`; three skips
  require Windows symlink privileges and three are opt-in GGUF cases whose
  configured-model subset then passed all 6 integration/example tests.
  Warnings are deprecated `sre_parse`/`sre_constants` imports in Lark.
- Native Core: strict workspace Clippy, locked workspace tests, and release
  build passed with Rust 1.94.0. The matching executable reports `Sona native
  0.16.0`.
- Proof: a real `0.16.0` Native Core execution produced and verified a schema-1
  receipt; it records Native Core, Python not involved, and fallback false.
- VS Code: under Node 20.19.5, compile, AI Console, Guide, and Runtime smokes
  passed; `npm audit --audit-level=moderate` found zero vulnerabilities. The
  rebuilt VSIX embeds version `0.16.0`, display name `Sona`, and passed archive
  inspection.
- Rebuilt-VSIX install smoke: an isolated VS Code profile installed and
  activated the package and detected the configured Sona `0.16.0` CLI. The
  Guide proposal walkthrough could not proceed because the test workspace was
  in Restricted Mode; no trust setting was changed and no edit was applied.
  The current package was rebuilt after updating patched transitive
  dependencies; the Node `20.19.5` compile, Guide/Runtime/AI Console smokes,
  packaging, and moderate-level audit all pass with zero reported advisories.
- Python distributions: versioned wheel and sdist built; extracted-archive
  installs with dependencies passed in clean Python 3.12.13 environments;
  `uv pip check`, CLI version, module import, syntax check, and hello execution
  all passed for both formats.
- Documentation and flagship examples: all 15 Python/Native manifest examples
  passed. The direct local-AI example loaded the hash-verified staged GGUF and
  returned a response from `llama-cpp 0.3.35` with local/no-fallback identity.
  With socket networking rejected in-process, the same local model also
  proposed a Sona replacement that passed deterministic validation.
  The three-step workflow example was interrupted, reopened inert, and
  explicitly resumed; the service example recovered with one bounded restart;
  the typed event/message example passed.
- User-provided acceptance: the authorized Guide proposal applied to the
  editor buffer only, and the before/after on-disk hash was unchanged.
  This was a development-host test, not an install-and-walkthrough of this
  rebuilt VSIX artifact.

Remaining gates are:

- Hosted Ubuntu, macOS, and Windows certification on the final source. The
  cross-platform workflow is prepared and locally syntax-checked, but remains
  uncommitted and is absent from the remote branch and `main`; it has not run
  against this source. The latest remote dispatch (`35985652111`) tested an
  older commit and all three jobs failed before running steps; GitHub exposes
  no job log, so it is not OS certification and the current failure cause is
  unconfirmed. Running hosted checks on this source requires uploading the
  candidate branch, which has not been authorized.
- The complete 12-part release demonstration has not yet been captured as one
  continuous acceptance run with networking disabled and a live approved Guide
  edit followed by workflow recovery, Guardian, and Proof checks. Individual
  local lanes and the user-reported editor acceptance passed, but that does
  not substitute for the integrated demo.
- The controlled Windows offline acceptance is **PASS**: Ethernet and Wi-Fi
  were administratively disabled, no connection profiles remained, Ollama was
  stopped, and the pinned GGUF was loaded directly. The model/runtime/example
  lane passed 6 tests and the Proof/Guardian/Guide compatibility lane passed
  279 tests. The user also confirmed the live VS Code approval and buffer-only
  apply; the disk hash was unchanged. This is local Windows evidence, not
  hosted OS certification.
- Guide buffer replacement uses the distinct `EDITOR.BUFFER_REPLACE` effect;
  it is never mapped to `FS.WRITE`, save, process execution, Guardian mutation,
  or Proof authority. Guardian remains optional when uninitialized; configured
  Guardian state must remain trusted at both capability preparation and
  consumption. The exact, five-second capability is held by the LSP and
  consumed once against opaque workspace/document hashes, document version,
  selection, original-source hash, candidate hash, and replacement hash.
  Selection and source state are rechecked immediately before and during the
  in-memory buffer operation. Focused tests cover changed resources, expiry,
  revocation, reuse, Guardian drift/errors, and no-save/no-execution behavior.
  The user-confirmed live VS Code acceptance demonstrates buffer-only apply and
  unchanged disk bytes; it is not an atomic OS boundary or durable Proof
  receipt.
- The patched dependency graph has not reached the default branch. The zero-
  vulnerability `npm audit` result applies to this development branch only;
  default-branch Dependabot alerts remain unresolved until that branch is
  updated.
- The exact candidate source is still uncommitted and not on the remote branch,
  so hosted jobs cannot yet certify this tree. The `0.16.0` source/extension
  version alignment and local artifacts are complete, but do not publish them
  as a fully certified cross-platform release until hosted checks pass.

## Previously built preview artifact (stale)

A prerelease-marked VSIX was built before the current durable-temporal-workflow
and Guide proposal-validation changes, without changing the project version:

- `sona-ai-native-programming-0.16.0-dev.3-node20.vsix`
- SHA-256: `28c1a2ba1c26635b9bf9e475c575b976893d6f7d36bbfdc073b8eaa442fbb329`

The wheel and source distribution are locally built validation artifacts. Their
availability does not certify installation or runtime behavior on other
operating systems. These artifacts do not include the current uncommitted
workflow changes and must not be treated as the completed 0.16.0 release
packages. Rebuild and verify packages only after the release scope and gates
are complete. Verify downloaded artifacts against their published hashes
before installation.

## Known limits

- Python remains the broad compatibility runtime; Native Core is not made the
  default by this release.
- Native Proof Mode remains Native-only and rejects fallback. Schema-1
  compatibility does not make Python executions equivalent to Native ones.
- The capability authority and effect journal are not a Python sandbox or an
  operating-system security boundary. Only Guide's in-memory editor-buffer
  path is connected to Guardian policy; other operations remain ungoverned by
  this adapter.
- Resource readings are caller-supplied; the resource reporter does not sample
  or enforce CPU/memory limits.
- Workflow time controls require the owner to poll due delays/deadlines and
  acknowledge cancellation; they do not provide a background scheduler,
  operating-system preemption, exact clock guarantees, or exactly-once work.
- The service registry is process-local; there is no cross-process service
  discovery.
- Native HTTP, remote attestation, signatures/PKI, and cloud services are out of
  scope.
- Linux/macOS and Android/iOS support are not established by this checkpoint.

## Documentation

- [0.16.0 architecture record](docs/plans/0.16.0-architecture-record.md)
- [Runtime effect, capability, and trust contracts](docs/spec/runtime/effects-capabilities-trust.md)
- [Durable workflow contracts](docs/spec/runtime/workflows.md)
- [Tasks and resource contracts](docs/spec/runtime/tasks-resources.md)
