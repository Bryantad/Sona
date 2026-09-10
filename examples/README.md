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
