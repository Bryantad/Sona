# Learn while you build

Sona 0.15.6 includes these commands for executable examples and lessons.

## Start with a real example

```bash
sona examples
sona examples run variables
sona examples run files --json
```

The schema-1 catalog at `sona/data/examples.json` is included in the wheel.
Program sources remain authoritative under `examples/`; the package build
copies only declared assets. A source archive contains those assets too.
Cloners and installed-package users run the same sources and expected-output
checks. Existing official filenames are retained.

Each run uses a fresh temporary working directory, then removes it. The files
example writes and reads `practice.txt` there, not in your current project.
The runner never removes `.sona` state from the original examples tree.
This is workspace isolation, **not an OS security sandbox**: the installed
runtime and shipped programs must still be trusted. Programs are selected by
catalog name, not an arbitrary file path. Each subprocess has a 30-second
deadline and a 64-KiB combined-output limit; stdin is closed.

Python examples use Sona's actual compatibility parser/runtime and do not
produce Native execution evidence. The checks compare exact output, exit
status, stderr, and any designated file roundtrip. Newline differences between
Windows and POSIX are normalized for textual checks.

## Explore, then practice

```bash
sona learn
sona learn loops
sona learn loops --mode expert
sona learn run loops
sona learn run files --no-profile
```

Nine initial topics are variables, conditions, loops, functions, collections,
modules, files, Guardian, and Proof Mode. Lesson explanations use the same
reviewed concept catalog as the CLI/LSP/editor, with Guided, Balanced, and
Expert detail. Exploring/listing lessons does not execute code or save state.

`learn run <topic>` explicitly runs the corresponding checked example. A pass
records only the topic's `learning` familiarity in `.sona/learning.json` in the
selected project (`--project-root`, default current directory). Existing
`comfortable` familiarity is preserved. Running a demonstration is not proof
of mastery, and Sona does not infer ability or medical state. There is no
percentage score or hidden encounter counter. Failed or unavailable practice
does not record progress. A profile-write failure is reported separately from
any successful execution checks.

`--no-profile` disables both reads and writes. Profile commands remain available
to inspect, edit, and reset familiarity and preferences:

```bash
sona guide profile --json
sona guide profile learn loops --familiarity comfortable
sona guide profile reset
```

No source, output, temporary path, receipt, or credential is saved in the
learning profile. The run's JSON output may contain transient execution and
verified-receipt facts; it is not the persisted profile.

## Native trust practice

```bash
sona examples run proof-mode
sona learn run guardian --no-profile
```

These require a matching `sona-native` on PATH or explicit `SONA_NATIVE_BINARY`.
The normal version preflight runs before Native execution. Missing/stale Native
Core fails clearly; no Python execution fallback or fabricated receipt is used.
Python coordinates the lesson and verification; the program recorded by Proof
Mode executes solely in Native Core.

The Proof Mode example prints a message, generates a real receipt, and checks it
with the existing verifier. The Guardian example initializes a **temporary**
default-deny project, checks and explains its policy, then requests a write even
with `--allow-fs-write`. The policy must deny the write, no file may appear, and
the valid Guardian-bound receipt must record `SONA-FS-005` and a denied
`FS.WRITE` effect. The existing Guardian verifier checks the baseline binding.

Thus Guardian practice can report **checks passed** while the receipt truthfully
reports **execution failed**. Receipt validity means self-consistency, not
producer authentication, signatures, host integrity, or remote attestation.
These disposable lessons do not retain receipts. Use the regular
[Proof Mode workflow](proof-mode.md) for evidence you want to keep.

## Executable documentation contract

The following blocks are designated executable by the preceding
`sona-example: <catalog-name>` marker. Tests require exact agreement with the
authoritative source and execute every manifest entry. Other snippets are
reference material unless explicitly designated; adding an executable marker
creates a CI obligation. This designation does not remove any existing official
example or trusted-workflow test from the gate.

<!-- sona-example: conditions -->
```sona
let ready = true;
if ready {
    print("Ready");
} else {
    print("Not ready");
}
```

<!-- sona-example: loops -->
```sona
let total = 0;
for value in [1, 2, 3] {
    print(value);
    total = total + value;
}
print("Total: " + total);
```

<!-- sona-example: collections -->
```sona
let values = [5, 10, 20];
let project = {"name": "Sona"};
print(project["name"]);
print(values[0]);
```

<!-- sona-example: files -->
```sona
import fs;
fs.write_text("practice.txt", "Sona file practice");
let content = fs.read_text("practice.txt");
print(content);
```

## Validation and failure contracts

```bash
python tools/run_examples.py --include-native
python -m pytest tests/examples tests/guide tests/lsp -q -ra
```

Without `--include-native`, the repository runner explicitly reports Native
examples as not run. CI must include the Native tests and all four existing
trusted workflows (the API workflow uses a local loopback fixture, not a remote
service). Package tests rebuild a wheel from the sdist and execute examples
outside the checkout. Matching-host CI success is required separately on
Windows, Linux, and macOS; a local run does not certify other platforms.

`--json` emits `schema_version: 1`. Run status is `passed`, `failed`, or
`unavailable`, with named boolean `checks`, actual `execution`, and optional
verified `receipt`/`guardian` facts. `progress_recorded` describes profile
persistence, not execution success. Exit code 0 means all requested work passed;
1 means an unavailable runtime, failed check, or profile error; argparse usage
errors exit 2.

| Identifier | Meaning |
| --- | --- |
| `SONA-EXAMPLE-001` | Unknown example/topic or invalid learning action |
| `SONA-EXAMPLE-002` | Invalid or missing catalog/asset |
| `SONA-EXAMPLE-003` | Runtime or temporary workspace unavailable |
| `SONA-EXAMPLE-004` | Time/output bound exceeded |
| `SONA-EXAMPLE-005` | Deterministic execution/workflow check failed |

Existing `SONA-NATIVE-LAUNCH-*` and `SONA-GUIDE-*` diagnostics retain their
meaning. Unknown names do not select arbitrary source, and raw operating-system
launch errors are not echoed as diagnostics.
