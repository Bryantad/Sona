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

The caller registers and inspects an artifact separately, then explicitly
selects the model identity for the service:

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
