# Local AI service — process-local contract

Status: experimental API for the Sona 0.16.0 development branch.

`LocalAIService` in `sona.intelligence.service` owns a local runtime adapter,
one configured model, one inference worker, and bounded request/stream queues.
It is an in-process service, not a child process, network daemon, cloud client,
or operating-system sandbox.

## Basic use

Install the optional direct GGUF runtime when using llama.cpp:

```powershell
python -m pip install "sona-lang[llama-cpp]"
```

Register and select an artifact through the CLI; no registry JSON editing is
required:

```powershell
sona model add D:\Models\qwen.gguf --id qwen-coder-local --context 16384 --device auto --set-default
sona model list
sona model inspect qwen-coder-local --verify-hash
```

The user registry is stored at `%SONA_HOME%\models.json` when `SONA_HOME` is
set, or `~/.sona/models.json` otherwise. `model add` validates the GGUF v2/v3
container structure and selected metadata, canonicalizes the artifact path,
and records its SHA-256. It derives architecture and common quantization labels
from the file and rejects caller-declared values or context limits that conflict
with the metadata. `model inspect --verify-hash` recomputes the digest and exits
unsuccessfully if the artifact changed. `sona model remove <id>` removes only
the registry entry and never deletes the model file. Registration does not
load or execute the model.

## Model inspection and preflight

`sona model inspect <id>` reads GGUF headers, selected metadata, and tensor
descriptors without loading tensor weights. JSON is the default; use
`--format text` for a concise terminal report. The report includes artifact
size, declared architecture/context/quantization, llama.cpp binding status,
host CPU and physical RAM, and best-effort accelerator information. Current
hardware probes report NVIDIA devices through `nvidia-smi`; Apple Silicon is
identified as unified memory without claiming a separate VRAM size. Other
accelerators may remain unknown.

The preflight blocks known static conflicts before model load, including a
configured context larger than the GGUF-declared context, an architecture
identity mismatch, or an explicit CUDA request when the installed binding was
not built for GPU offload or no NVIDIA device is observed. The `auto` device
currently resolves to CPU. These checks do not establish architecture support
inside the installed llama.cpp build, available-memory headroom, actual load
success, OS-level resource enforcement, or performance. A preflight pass is
not a compatibility certification; only an explicit model load can confirm
that the selected artifact and runtime work together on that host.

The Python caller then explicitly selects the registered model identity for
the service:

```python
from sona.intelligence import LlamaCppRuntimeAdapter, LocalAIService

with LocalAIService(LlamaCppRuntimeAdapter()) as service:
    service.load_model(model_identity)
    result = service.infer(request)
```

`model_identity` must select `provider_id="local"` and `runtime_id="llama-cpp"`
for this adapter. The service never redirects a failed local request to
Ollama, a remote API, or another provider.

## Lifecycle and residency

The service model lifecycle is `OFF → LOADING → READY → ACTIVE → IDLE`.
Configured-but-unloaded models use `SLEEPING`; unrecoverable load/runtime
failures use `ERROR`. Only one model is resident at a time. Loading another
model is explicit and releases the prior model before loading the replacement.

Residency policies:

| Policy | Idle behavior |
| --- | --- |
| `automatic` (default) | Unload after the configured idle timeout; keep identity and reload on the next request. |
| `while_coding` | Keep resident while the host reports coding activity; otherwise apply idle timeout. |
| `always_loaded` | Do not evict for idleness; release on explicit unload or service close. |
| `manual` | Do not evict for idleness; release on explicit unload or service close. |

The default idle timeout is 300 seconds. A service context manager or
`close(timeout=...)` should be used to release native resources. `close`
cooperatively cancels active work and reports false if the runtime has not
stopped or cleanup failed by the timeout. It does not force-kill native code.
Cleanup is retried by a later `close()` call if native unload failed.

Residency lasts only for the current Python process. Reopening a process does
not restore or automatically load a model; the application must select it
again. The model registry may persist model identities, but that does not
grant execution authority or cause loading.

## Queue, results, streaming, and cancellation

The default service has four pending slots and one active worker. Pending
queue overflow raises `InferenceQueueFull`; accepted jobs receive UUID-backed
IDs and can be queried with `state(job_id)`, canceled with `cancel(job_id)`,
or collected with `wait(job_id, timeout=...)`. A wait timeout only stops the
caller from waiting; it does not cancel the inference. Queued cancellation is
terminal immediately; running cancellation is cooperative at runtime-defined
checkpoints.

`stream(request)` uses the same worker and a bounded per-stream chunk buffer
(32 chunks by default). If the consumer stops iterating, the service cancels
that job. Stream sequences are checked for request identity and order. Blocking
backpressure is used instead of unbounded buffering or silent chunk loss.

Each `InferenceRequest.timeout_seconds` controls runtime execution after the
job starts; it does not include time spent waiting in the service queue. Native
prompt evaluation may delay observing a cooperative deadline or cancellation.

## Instruction-style and structured output

`InferenceRequest` may optionally include a `system_prompt` (up to 16 KiB) and
an `output_json_schema` UTF-8 JSON object string (up to 16 KiB). With a system
prompt, the direct llama.cpp adapter uses its model-specific chat completion
handler and checks timeout and cancellation between streamed output chunks. It
reserves 128 context tokens for chat-template overhead. Without a system
prompt, the raw completion API remains selected; with no system prompt or
schema, the existing raw completion behavior is unchanged. A JSON schema is
compiled to a llama.cpp grammar; structured generation uses temperature zero.
Missing chat-template or grammar support fails closed instead of changing
providers or reverting to unconstrained output. Native prompt evaluation can
still delay observing a deadline.

Guide edit proposals use this mode to require one JSON object containing only a
`replacement` string. The grammar enforces that outer shape, not the semantic
correctness of the proposed code. The proposal remains untrusted: the Guide
frontend performs a separate read-only Sona syntax check, then VS Code shows a
diff and waits for explicit user approval before requesting a separate
`EDITOR.BUFFER_REPLACE` capability for the exact in-memory candidate.
Syntax validity does not establish that an edit is the one the user intended,
does not execute it, and does not grant filesystem or Guardian authority. After
approval, a five-second, exact-resource `EDITOR.BUFFER_REPLACE` capability is
prepared and consumed once immediately before the in-memory edit. Guardian is
optional when uninitialized; when configured, its trust check must be healthy
at both authorization stages. This effect is distinct from `FS.WRITE`, does not
save the file, and grants no other operation. See the
[effect/capability trust contract](effects-capabilities-trust.md).

## Resource and trust boundary

`LocalAIServiceLimits` enforces:

- bounded pending jobs;
- one inference at a time;
- maximum configured model context;
- maximum output tokens per request;
- bounded streaming chunks and retained job history.

The service reports queue, concurrency, model-context, and output limits as
`ENFORCED`. Host RAM and accelerator-memory limits are reported as
`UNSUPPORTED` with amount zero; these are not measured or enforced. The API
does not imply resource isolation or guaranteed hardware availability.

Prompts and generated text remain in memory for the call/job result. They are
not added to Proof schema-1 or persisted by this service. A runtime error
causes best-effort model unload, returns a stable service diagnostic, and
requires explicit model reload. Native Proof Mode and Guardian remain separate
authorities and are not modified by inference.
