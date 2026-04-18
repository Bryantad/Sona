# Memory Integration Troubleshooting

## Symptom Split

The external-memory integration has two different failure surfaces:

- `import memory` fails only when the module or bridge itself cannot load.
- `memory.*` fails at call time when memory is disabled, misconfigured, unauthorized, or unreachable.

That distinction is intentional.

## Common Problems

### `memory.*` says memory is unavailable

Check:

- `SONA_MEMORY_ENABLED=true`
- `SONA_MEMORY_BASE_URL` is set
- `SONA_MEMORY_TOKEN` is set
- `SONA_MEMORY_NAMESPACE` is the namespace you expect

### `memory.*` raises transport or HTTP errors

Check:

- the memory server is running
- the base URL is correct
- the bearer token matches a configured service or operator principal
- the namespace is authorized for that token

### `import memory` fails immediately

This is not a runtime configuration problem. Check:

- `stdlib/memory.smod` exists
- `sona/stdlib/native_memory.py` exists
- the native bridge loads without syntax or import errors

### Demo output is unexpected

The documented positive-path demo namespace is:

```text
/projects/sona-demo
```

The fixed demo record is:

```text
content = "demo memory seeded from sdk"
subject = "sona-demo"
kind = "demo_seed"
```

If `memory_second_run.sona` prints `No prior demo memory found.`, one of these is wrong:

- the record was not seeded
- the namespace is not `/projects/sona-demo`
- the record content, subject, or kind does not match the fixed demo values

## Resetting the Demo

This phase does not support deleting memory. Use a new namespace instead:

```powershell
$env:SONA_MEMORY_NAMESPACE = "/projects/sona-demo-negative-001"
sona run examples/memory_second_run.sona
```

Expected output:

```text
No prior demo memory found.
```
