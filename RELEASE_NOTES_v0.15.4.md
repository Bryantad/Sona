# Sona 0.15.4 — Native Proof, Guardian Trust, and Governed AI Review

Sona 0.15.4 introduces an end-to-end local trust workflow for Native Core:
create redacted execution evidence, bind it to a Guardian-tracked project
baseline, verify it, record a clean-state attestation, and optionally ask a
governed AI reviewer to explain only the verified redacted facts.

```text
reviewed project → Guardian baseline → Native Proof receipt
                 → verify → attest → optional governed AI review
```

The AI layer is deliberately outside the trust chain. It can explain evidence;
it cannot create, alter, verify, or strengthen that evidence.

This release also hardens Sona's standard library into a documented runtime
contract while preserving 0.15.3 Python-compatible behavior. Native Core
remains a preview, and Python remains Sona's compatibility engine.

## Highlights

This workflow uses two command surfaces:

| Command | Role |
| --- | --- |
| `sona` | Python-compatible CLI, Guardian, package tools, and developer intelligence |
| `sona-native` | Convenient installed alias for the standalone Native Core executable |
| `sona.exe` | Executable filename inside the Windows Native Core ZIP |

### Native Proof Mode

Native Core can now execute a `.sona` program or source-backed `.sbc` container
and publish a `sona.native-proof.schema-1` JSON receipt:

```powershell
sona-native proof .\app.sona `
  --receipt .\.sona\receipts\app-proof.json `
  --engine native `
  --summary
```

- Receipts identify the exact input bytes, engine, granted capabilities,
  ordered observable effects, execution outcome, diagnostics, and hashed
  stdout/stderr.
- Receipts are canonical, self-hashed, redacted, and published without
  overwriting an existing destination.
- Source text, raw paths, output bodies, stdin values, credentials,
  environment values, and raw operating-system error text are never stored.
- `--summary` adds a concise, professional terminal confirmation after the
  receipt is saved. The summary is written to stderr so program stdout remains
  pipeline-friendly.
- `PROOF-001` through `PROOF-008` provide stable infrastructure diagnostics;
  program parser, VM, runtime, and capability diagnostics keep their existing
  identifiers.

### Guardian-bound execution evidence

Add `--guardian-root` to require the program to match an initialized Guardian
baseline before Native Core executes it:

```powershell
sona-native proof .\app.sona `
  --receipt .\.sona\receipts\app-proof.json `
  --engine native `
  --guardian-root . `
  --summary
```

Native Core reads the minimum trusted Guardian state directly. It does not
import Python, invoke Guardian, mutate Guardian state, or record the project
path in the receipt. A missing, stale, inconsistent, or untracked baseline
fails with `PROOF-008` before program execution.

The Python-compatible CLI then provides four explicit downstream operations:

- `sona guardian proof verify` checks canonical storage, the receipt self-hash,
  Native/no-Python identity, the Guardian anchor, and baseline-tracked program
  identity. Verification is read-only.
- `sona guardian proof attest` repeats verification, requires a successful
  execution, requires the live project to remain clean, and appends a redacted
  local attestation record.
- `sona guardian proof review` analyzes a verified redacted packet through a
  governed reviewer.
- `sona guardian proof history` shows recent local Proof attestations.

### Governed AI review

Guardian Proof review verifies evidence before any provider is selected or
called. The review packet contains only:

- the receipt hash;
- the execution status and exit code;
- the redacted Guardian anchor; and
- whether a local attestation has been recorded.

Sona returns a SHA-256 identity for that exact packet. It sends no project or
receipt paths, source, selected workspace files, output bodies, environment
values, or credentials as review context.

The deterministic local reviewer is the reproducible default. Configured
local Ollama is available with `--provider ollama`. Remote providers require
explicit selection, `--allow-network`, and a governance policy that permits
the route. Provider output is always labeled advisory, writes no AI task
receipt, and adds no verification or attestation claim.

### Standard-library cohesion and runtime capabilities

- A schema-2 manifest is now the authority for 146 preserved public modules,
  including signatures, compatibility dispositions, diagnostics, and support
  classifications.
- The certified foundation covers `collection`, `date`, `fs`, `http`, `io`,
  `json`, `math`, `random`, `stdin`, `string`, and `time`.
- Canonical filesystem, HTTP, JSON, random, stream, input, string, date, and
  time APIs now use stable structured diagnostic families.
- Python-compatible normal runs preserve filesystem and network behavior;
  `--safe` confines reads to the project root and denies secret reads, writes,
  and network access.
- Native Core remains console-only by default. Filesystem and network policy
  require explicit `--allow-fs-read`, `--allow-fs-write`, and
  `--allow-network` flags.
- Native HTTP remains intentionally unavailable in 0.15.4 and emits
  `SONA-HTTP-005` instead of silently falling back to Python. Native
  `collection` and `random` support remain classified as partial.

## Install the release assets

### Python-compatible CLI and Guardian

Python 3.11 and 3.12 are supported:

```powershell
python -m pip install .\sona_lang-0.15.4-py3-none-any.whl
sona --version
```

Expected version: `Sona 0.15.4`.

### Windows Native Core

The Native Core ZIP contains one standalone executable named `sona.exe`:

```powershell
Expand-Archive `
  .\sona-native-0.15.4-windows-x86_64.zip `
  -DestinationPath .\sona-native-0.15.4-windows-x86_64

.\sona-native-0.15.4-windows-x86_64\sona.exe --version
```

The guides use `sona-native` as a convenient installed alias. If you run the
ZIP directly, substitute the full path to its `sona.exe`.

### Linux and macOS Native Core

The cross-platform release workflow builds and executes architecture-specific
Native Core candidates on their matching hosts:

| Host | Native Core asset |
| --- | --- |
| Linux x86-64 | `sona-native-0.15.4-linux-x86_64-musl.tar.gz` |
| Linux ARM64 | `sona-native-0.15.4-linux-aarch64-musl.tar.gz` |
| macOS Intel | `sona-native-0.15.4-macos-x86_64.tar.gz` |
| macOS Apple Silicon | `sona-native-0.15.4-macos-aarch64.tar.gz` |

Attach these files only after the final-commit workflow passes. The Linux
artifacts are static musl builds. The macOS candidates remain unsigned until a
separate Apple Developer ID signing and notarization gate is completed.

The wheel, source distribution, and VSIX are portable artifacts; separate
copies are not built per operating system. The workflow installs and tests the
same wheel bytes with Python 3.11 and 3.12 on all five desktop targets.

### VS Code extension

```powershell
code --install-extension .\sona-ai-native-programming-0.15.4.vsix
```

The extension documents the 0.15.4 Proof and Guardian workflow. Its AI Console
remains backend-focused; this release does not redesign that UI.

## Try the complete trust chain

Use a dedicated child directory rather than initializing Guardian directly in
the system temporary-directory root:

```powershell
$native = (Get-Command sona-native).Source
# ZIP users can instead resolve the extracted sona.exe before Set-Location:
# $native = (Resolve-Path .\sona-native-0.15.4-windows-x86_64\sona.exe).Path

$project = Join-Path $env:TEMP `
  ("sona-0154-proof-{0}" -f [guid]::NewGuid())
New-Item -ItemType Directory -Path $project | Out-Null
Set-Location $project

'print("Sona 0.15.4 Guardian-bound Proof: OK")' |
  Set-Content -LiteralPath .\hello.sona -Encoding ascii
New-Item -ItemType Directory -Path .\.sona\receipts | Out-Null

sona guardian init --project-root .
sona guardian verify --project-root .

$receipt = Join-Path (Resolve-Path .\.sona\receipts) `
  ("hello-proof-{0}.json" -f [guid]::NewGuid())

& $native proof .\hello.sona `
  --receipt $receipt `
  --engine native `
  --guardian-root . `
  --summary

sona guardian proof verify `
  --project-root . `
  --receipt $receipt

sona guardian proof attest `
  --project-root . `
  --receipt $receipt

sona guardian proof review `
  --project-root . `
  --receipt $receipt `
  --provider deterministic

sona guardian proof history --project-root . --limit 10
```

The expected status progression is `initialized` → `ok` → `verified` →
`attested` → `reviewed`.

## Compatibility

No breaking language change is intended in 0.15.4.

- Valid 0.15.3 Python-compatible programs, implicit final-statement function
  values, cognitive runtime behavior, existing Guardian interfaces, and
  workspace-module precedence are preserved.
- Existing public modules remain importable, and canonical aliases remain
  quiet for the rest of the 0.15.x line.
- Proof, Guardian binding, attestation, and review are additive and opt-in.
- Proof Mode observes Native Core without changing ordinary `run`, `exec`, VM,
  capability, or language semantics.

## Release assets

| Asset | Purpose |
| --- | --- |
| `sona_lang-0.15.4-py3-none-any.whl` | Python wheel for the `sona` CLI, Guardian, and compatibility runtime |
| `sona_lang-0.15.4.tar.gz` | Python source distribution; separate from GitHub's automatic source archive |
| `sona-native-0.15.4-windows-x86_64.zip` | Standalone Windows x86-64 Native Core executable |
| `sona-native-0.15.4-linux-x86_64-musl.tar.gz` | Static Linux x86-64 Native Core executable |
| `sona-native-0.15.4-linux-aarch64-musl.tar.gz` | Static Linux ARM64 Native Core executable |
| `sona-native-0.15.4-macos-x86_64.tar.gz` | macOS Intel Native Core executable |
| `sona-native-0.15.4-macos-aarch64.tar.gz` | macOS Apple Silicon Native Core executable |
| `sona-ai-native-programming-0.15.4.vsix` | VS Code extension package |
| `sona-0.15.4-platform-test-kit.zip` | Cross-platform machine verifier and instructions |
| `sona-0.15.4-release-manifest.json` | Source commit and host-tested desktop matrix |
| `SHA256SUMS.txt` | SHA-256 authority for the assembled release candidate |

Do not embed any Native Core archive in the wheel or VSIX. Each native build is
a separate GitHub Release asset tied to its own host evidence.

## Documentation

- [Native Proof Mode Guide](docs/guides/proof-mode.md)
- [Guardian Guide](docs/guides/guardian.md)
- [Using Native Proof and Guardian Together](docs/guides/proof-and-guardian.md)
- [Platform Installation and Testing](docs/guides/platform-installation-and-testing.md)
- [Native Proof Mode Reference](docs/reference/native-proof-mode.md)
- [Guardian Reference](docs/GUARDIAN_REFERENCE.md)
- [0.15.4 Implementation Report](docs/release/0.15.4-implementation-report.md)

## Validation summary

The implementation was validated across the language, trust chain, Native
Core, package, and extension surfaces:

- 424 Python tests passed with the two host-limited native gate files excluded;
  the only accepted warnings were two Python 3.12 deprecations from pinned
  `lark-parser==0.12.0`.
- 16 focused Guardian Proof AI tests passed, including rejection before
  provider routing and deterministic/mocked-Ollama review paths.
- The real Native Proof → Guardian verify → attest → deterministic review flow
  passed, together with the documented drift, governed recovery, and final
  clean-verification workflows.
- All 9 official examples and all 3 runtime probes passed.
- Rust formatting and locked Clippy passed with zero warnings; all 29 Rust unit
  tests passed.
- The bounded differential corpus completed 40 executions with 0 failures;
  the standard-library corpus completed 20 executions with 0 failures.
- Native standalone validation completed 16 checks with 0 failures.
- Wheel, source distribution, Native ZIP, and VSIX builds, inspections, clean
  installs, and smoke tests passed. The VSIX production dependency audit
  reported 0 high, 0 critical, and 0 total vulnerabilities.
- The cross-platform packager, deterministic archive checks, exact-candidate
  assembler, and machine verifier pass their local unit suite. The real Windows
  verifier also passed the wheel/sdist/VSIX inspection and complete Native
  Proof → Guardian verify → attest → deterministic review workflow.

See the implementation report for the precise commands and scope. Final
publication certification still requires the final-commit workflow to pass on
Windows x86-64, Linux x86-64/ARM64, and macOS Intel/Apple Silicon with Python
3.11/3.12. macOS signing and notarization remain a separate publication gate.

## Trust and preview limits

- Native Proof is redacted, self-hashed, and integrity-checkable
  evidence. It is not signer identity, trusted timestamping, trusted-hardware
  proof, operating-system integrity proof, remote attestation, or a claim of
  Python/Native semantic parity.
- Guardian establishes project-local trust. It does not protect against an
  actor able to replace both the receipt and local Guardian state, and it is
  not antivirus software or a remote backup service.
- AI review is advisory analysis after verification. It cannot verify, attest,
  mutate, or expand the evidence claim.
- Native Core remains a preview; Native HTTP and serialized native instruction
  streams remain future work.
- Android and iOS are compile-only experiments in 0.15.4, not supported mobile
  release targets. The Linux ARM64 archive must not be relabeled as Android,
  and no standalone iOS CLI or app package is provided.
