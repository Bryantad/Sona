# Sona Official Examples

These examples are the stable `0.14.x` onboarding surface for docs and tests.
Do not rename or remove them without updating `docs/QUICKSTART.md`,
`docs/STDLIB_REFERENCE.md`, and the example tests.

## Examples Validation Rule

- Official examples must exist in the source repository.
- `python tools/run_examples.py` must pass against the repo copy.
- Examples are not required to be present in installed packages.

## Official Suite

Run every official example:

```bash
python tools/run_examples.py
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

## Isolation Rules

- Examples do not require external services.
- Examples do not require persistent memory state.
- Examples do not depend on artifacts from previous runs.
- `tools/run_examples.py` runs copies in a temporary directory and cleans `.sona`
  runtime artifacts before and after execution.
