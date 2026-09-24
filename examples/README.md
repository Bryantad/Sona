# Sona Official Examples

These examples are the stable `0.15.x` onboarding surface for docs and tests.
Do not rename or remove them without updating `docs/QUICKSTART.md`,
`docs/STDLIB_REFERENCE.md`, and the example tests.

## Examples Validation Rule

- Official examples must exist in the source repository.
- `python tools/run_examples.py` must pass against the repo copy.
- The schema-1 manifest at `sona/data/examples.json` selects the installed
  examples. Wheels include copies of the declared sources; sdists retain their
  authoritative source files. `sona examples run <name>` uses the same checks.

## Official Suite

Run every official example:

```bash
python tools/run_examples.py --include-native
```

Run one example:

```bash
sona run examples/hello.sona
```

## Files

| File | Purpose |
| --- | --- |
| `hello.sona` | Smallest runnable Sona program. |
| `variables_math.sona` | Variables and arithmetic. |
| `functions.sona` | Function definitions, returns, and calls. |
| `control_flow.sona` | Conditionals and loops. |
| `stdlib_math.sona` | Stable `math` module use. |
| `stdlib_string.sona` | Stable `string` module use. |
| `stdlib_json.sona` | Stable `json` module use. |
| `stdlib_fs.sona` | Stable `fs` module use without modifying files. |
| `calculator.sona` | Small multi-function tool. |

## Trusted workflows

The [trusted workflow examples](trusted-workflows/README.md) demonstrate four
task-oriented paths: a controlled AI-proposal handoff, auditable calculation,
a real Python-compatible loopback API call with Native Proof explicitly
deferred, and a bounded local deployment-evidence reference.

## Isolation Rules

- Examples do not require remote services; the service-API workflow has a local
  loopback fixture.
- Examples do not require persistent memory state.
- Examples do not depend on artifacts from previous runs.
- `tools/run_examples.py` runs copies in fresh temporary directories and removes
  those directories only. Original `.sona` state is never cleaned.
- Without `--include-native`, it runs the Python catalog and explicitly reports
  Native examples as not run. Guardian/Proof Mode practice requires matching
  Native Core and never falls back to Python execution.

See [learning and examples](../docs/guides/learning-and-examples.md) for the
installed CLI, nine initial lessons, local progress, and executable-doc contract.

## 0.16.0 runtime demonstrations (development)

These Python API examples are separate from the installed `.sona` lesson
catalog; they demonstrate the current experimental runtime contracts directly.

| Directory | Demonstrates | Infrastructure |
| --- | --- | --- |
| [`local-ai`](local-ai/README.md) | Direct GGUF inference through llama.cpp, with no Ollama/cloud fallback. | Optional local GGUF file and `llama-cpp-python`. |
| [`durable-workflow`](durable-workflow/README.md) | Three dependent steps, process interruption, inert reopen, and explicit recovery. | None; writes only to its selected journal root. |
| [`supervised-service`](supervised-service/README.md) | One bounded service restart and cooperative shutdown. | None; in-process threads. |
| [`events`](events/README.md) | Typed event validation and a bounded typed-message channel. | None. |

`tests/examples/test_runtime_examples_0160.py` runs the three infrastructure-free
demonstrations. The direct-model example runs when CI provides `SONA_TEST_GGUF`;
otherwise that single integration case is explicitly skipped.
