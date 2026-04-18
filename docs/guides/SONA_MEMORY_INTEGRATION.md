# Sona Memory Integration

This guide documents the current external-memory integration for CLI file runs.

## What This Covers

- `sona run <file>` integration with the external memory server
- strict `memory.*` behavior versus best-effort lifecycle instrumentation
- the exact demo flow for `/projects/sona-demo`
- the expected runtime event order for debugging

## Environment

Required when external memory is enabled:

```powershell
$env:SONA_MEMORY_ENABLED = "true"
$env:SONA_MEMORY_BASE_URL = "http://127.0.0.1:8000"
$env:SONA_MEMORY_TOKEN = "service-token"
$env:SONA_MEMORY_NAMESPACE = "/projects/sona-demo"
```

Optional:

```powershell
$env:SONA_MEMORY_AGENT_ID = "sona.interpreter.sona-demo"
$env:SONA_MEMORY_TIMEOUT_SECONDS = "10"
$env:SONA_MEMORY_AUTO_REFLECT = "true"
```

Fallbacks when optional values are not set:

- namespace: `SONA_MEMORY_NAMESPACE` -> `/projects/<project_root_name>` -> `/projects/default`
- agent ID: `SONA_MEMORY_AGENT_ID` -> `sona.interpreter.<project_root_name>` -> `sona.interpreter.default`

## Invocation

Primary CLI form from the Sona repo root:

```powershell
sona run examples/memory_second_run.sona
```

Fallback from the Sona repo root:

```powershell
python -m sona.cli run examples/memory_second_run.sona
```

From another working directory, use the repo-local interpreter plus an absolute file path:

```powershell
$sonaRepo = "F:\SonaMinimal"  # adjust if cloned elsewhere
& "$sonaRepo\.venv\Scripts\python.exe" -m sona.cli run "$sonaRepo\examples\memory_second_run.sona"
```

## Behavior Contract

- Lifecycle instrumentation is best-effort. Failure to emit lifecycle events does not fail the user program.
- Direct `memory.*` calls are strict. If memory is disabled, misconfigured, or unreachable, the `memory.*` call raises at call time.
- `import memory` fails only for ordinary module or bridge load errors. Runtime memory misconfiguration does not break the import by itself.
- One top-level CLI run uses one runtime memory context, one session ID, one trace ID, and one monotonic `sequence_no` stream.

## Expected Event Timeline

For a normal demo flow, expect this order:

```text
session.started
trace.opened
message.user_received
tool.call_requested
tool.call_succeeded
optional message.model_emitted
trace.closed
session.ended
optional reflection.run_requested
```

`message.model_emitted` is omitted for silent runs that do not produce a top-level visible result.

## Demo Flow

The documented demo namespace for this phase is:

```text
/projects/sona-demo
```

### Pure Sona Demo

From the Sona repo root:

```powershell
$env:SONA_MEMORY_ENABLED = "true"
$env:SONA_MEMORY_BASE_URL = "http://127.0.0.1:8000"
$env:SONA_MEMORY_TOKEN = "service-token"
$env:SONA_MEMORY_NAMESPACE = "/projects/sona-demo"

sona run examples/memory_first_run.sona
sona run examples/memory_second_run.sona
```

Expected visible output:

```text
Recorded demo memory.
Prior demo memory found.
```

### Shared-Backend Demo

From the Sona repo root, seed the shared backend with the Python SDK example from the memory-server repo, then run the Sona reader:

```powershell
$memoryRepo = "F:\cognitive infastructure\persistent_memory_project"  # adjust if cloned elsewhere
$env:SONA_MEMORY_ENABLED = "true"
$env:SONA_MEMORY_BASE_URL = "http://127.0.0.1:8000"
$env:SONA_MEMORY_TOKEN = "service-token"
$env:SONA_MEMORY_NAMESPACE = "/projects/sona-demo"

python "$memoryRepo\examples\sdk_seed_memory.py"
sona run examples/memory_second_run.sona
```

Expected visible output from the Sona run:

```text
Prior demo memory found.
```

## Exact Demo Records

The fixed demo record is:

```text
content = "demo memory seeded from sdk"
subject = "sona-demo"
kind = "demo_seed"
```

`memory_second_run.sona` searches specifically for that record using the known content plus `subject = "sona-demo"` and `kind = "demo_seed"`. It does not branch on broad memory presence.

## Resetting the Demo

This phase does not include a delete or reset API. To force a clean run, switch to a new namespace:

```powershell
$env:SONA_MEMORY_NAMESPACE = "/projects/sona-demo-negative-001"
sona run examples/memory_second_run.sona
```

Expected visible output:

```text
No prior demo memory found.
```

## OpenAI MCP Demo

The external-provider proof uses a separate namespace:

```text
/projects/openai-mcp-demo
```

This proof uses a **scoped provider demo wrapper**, not the long-term generic MCP architecture.

The locked OpenAI demo contract lives in:

```text
F:\cognitive infastructure\persistent_memory_project\docs\guides\OPENAI_MCP_DEMO_CONTRACT.md
```

After the OpenAI-side write succeeds through the scoped MCP wrapper, use this repo-local absolute-path form:

```powershell
$sonaRepo = "F:\SonaMinimal"  # adjust if cloned elsewhere
$env:SONA_MEMORY_ENABLED = "true"
$env:SONA_MEMORY_BASE_URL = "http://127.0.0.1:8000"
$env:SONA_MEMORY_TOKEN = "service-token"
$env:SONA_MEMORY_NAMESPACE = "/projects/openai-mcp-demo"
& "$sonaRepo\.venv\Scripts\python.exe" -m sona.cli run "$sonaRepo\examples\openai_memory_reader.sona"
```

Expected visible output:

```text
OpenAI demo memory found.
```

`openai_memory_reader.sona` searches only for the exact deterministic contract record. Unrelated memories in the same namespace should not trigger the positive branch.

For the OpenAI proof, this absolute-path command is the source-of-truth invocation because it avoids working-directory mistakes.

## Ollama Offline Demo

The local/offline provider proof uses a separate namespace:

```text
/projects/ollama-offline-demo
```

The locked Ollama demo contract lives in:

```text
F:\cognitive infastructure\persistent_memory_project\docs\guides\OLLAMA_OFFLINE_DEMO_CONTRACT.md
```

After the local Ollama write succeeds through the memory-server demo script, use this repo-local absolute-path form:

```powershell
$sonaRepo = "F:\SonaMinimal"  # adjust if cloned elsewhere
$env:SONA_MEMORY_ENABLED = "true"
$env:SONA_MEMORY_BASE_URL = "http://127.0.0.1:8000"
$env:SONA_MEMORY_TOKEN = "service-token"
$env:SONA_MEMORY_NAMESPACE = "/projects/ollama-offline-demo"
& "$sonaRepo\.venv\Scripts\python.exe" -m sona.cli run "$sonaRepo\examples\ollama_memory_reader.sona"
```

Expected visible output:

```text
Ollama offline demo memory found.
```

`ollama_memory_reader.sona` searches only for the exact deterministic contract record. Unrelated memories in the same namespace should not trigger the positive branch.
