# Sona 0.15.6 — Cognitive Developer Experience

Sona 0.15.6 is the **Learn while you build** release. It adds Sona Guide, a
deterministic explanation and learning layer that makes compiler, runtime,
Proof Mode, and Guardian output easier to understand without changing the
underlying facts.

These notes describe the 0.15.6 release candidate. The authoritative source
has completed its version sweep and the final VSIX has been rebuilt locally.
Final publication still requires the remaining portable/Native artifact
rebuilds and matching-host Windows, Linux, and macOS certification.

No Sona syntax change is introduced. Existing 0.15.5 commands, valid project
state, Proof Mode schema-1 receipts, and Guardian workflows remain compatible.

## Highlights

### Sona Guide

Sona Guide explains existing diagnostics and trust-chain facts at the amount of
detail the developer selects:

```bash
sona why SONA-RUNTIME-003
sona why SONA-RUNTIME-003 --mode balanced
sona why PROOF-VERIFY-005 --style technical --json
```

The same canonical diagnostic or checked fact is preserved in Guided, Balanced,
and Expert presentations. These modes change explanation density only; they do
not create new compiler facts, weaken diagnostics, or infer anything about the
developer.

### Focus Mode and deterministic cascades

`sona focus` groups reviewed diagnostic cascades for presentation while keeping
the full canonical diagnostic list available in machine-readable output:

```bash
sona focus app.sona
sona focus app.sona --density complete --json
```

The initial cascade table is intentionally small. It can group downstream
parse/name noise after an unclosed delimiter, but it does not claim broad
compiler causality or delete diagnostics from complete output.

### Preview-first quick fixes

`sona fix` offers source edits only when a reviewed deterministic rule can
identify an exact edit:

```bash
sona fix app.sona --diagnostic-id SONA-RUNTIME-003 --name quant --line 3 --column 21
sona fix app.sona --rule stdlib-api-migration
```

Preview is the default. Applying a fix requires `--apply`, and stale-file
protection refuses the edit if the expected original text no longer matches.
The first fix rules cover closest unambiguous visible bindings and the reviewed
stdlib migration from deprecated file APIs to `fs.read_text` / `fs.write_text`.

### Local learning profile

Sona Guide can store explicit project-local preferences and concept
familiarity in `.sona/learning.json`:

```bash
sona guide profile
sona guide profile set --mode balanced --density focused
sona guide profile learn loops --familiarity learning
sona guide profile reset
```

The profile is local, bounded, inspectable, and resettable. It does not store
source text, file paths, output bodies, credentials, receipts, or inferred
medical state.

### Executable examples and lessons

The new examples surface lets developers run checked programs by name:

```bash
sona examples
sona examples run variables
sona learn
sona learn run proof-mode
```

The initial catalog covers variables, conditions, loops, functions,
collections, modules, files, Guardian, and Proof Mode. Examples execute through
the real Sona runtime. Proof Mode and Guardian lessons use Native Core and the
shared verifier when a matching native executable is available; they do not
fall back to Python or fabricate receipts.

### Proof Mode and Guardian explanations

Sona Guide can render checked Proof Mode and Guardian facts in a beginner
friendly format:

```bash
sona guide proof receipt.sproof
sona guide guardian --project-root .
```

These explanations describe verified fields only. They do not strengthen a
receipt, create attestation, add signer identity, or reinterpret Guardian
policy beyond the checked data.

### VS Code and LSP integration

The VS Code extension now uses the shared Guide contracts for diagnostic
explanations, focused diagnostics, safe code-action previews, lessons, checked
Proof Mode/Guardian explanations, and neutral display preferences. The
extension keeps trust-chain verification delegated to the Sona CLI/shared
verifier instead of reimplementing receipt semantics in TypeScript.

Runtime diagnostics produced by `sona run --json` are accepted by the extension
only when workspace trust, saved-source identity, source hash, and document
version checks agree.

### Native command selection hardening

The Python CLI probes the resolved Native Core executable before delegated
Native Proof Mode execution. Version mismatches fail before execution with a
stable diagnostic and redacted remediation. The stale stdlib migration metadata
now points to the canonical Native APIs, `fs.read_text` and `fs.write_text`.

## Assurance boundary

Proof Mode provides deterministic, privacy-conscious execution evidence for
fields emitted by Sona. Guardian provides local policy and baseline checks
around trusted Sona workflows.

Current 0.15.6 work does not provide:

- signer or operator identity;
- a trusted timestamp;
- a trusted execution environment or operating-system integrity proof;
- hardware or remote attestation;
- PKI, certificate roots, or package signing;
- protection against replacing and re-hashing an entire receipt; or
- a claim that Python-compatible and Native executions are semantically equal.

Sona Guide is also outside the verification chain. It explains canonical facts;
it does not generate evidence, verify evidence, or make policy decisions.

## Installation

The swept 0.15.6 candidate uses these installation commands:

```bash
python -m pip install sona_lang-0.15.6-py3-none-any.whl
sona --version
```

VS Code:

```bash
code --install-extension sona-ai-native-programming-0.15.6.vsix
```

Proof Mode execution also requires the Native Core archive matching the host.
Verify every downloaded artifact against `SHA256SUMS.txt` before installation.

## Release candidate artifacts

| Artifact | Purpose |
| --- | --- |
| `sona_lang-0.15.6-py3-none-any.whl` | Python-compatible CLI, Sona Guide, Guardian, LSP, SPM, and runtime |
| `sona_lang-0.15.6.tar.gz` | Python source distribution |
| `sona-ai-native-programming-0.15.6.vsix` | VS Code extension |
| `sona-native-0.15.6-windows-x86_64.zip` | Windows x86-64 Native Core |
| `sona-native-0.15.6-linux-x86_64-musl.tar.gz` | Linux x86-64 Native Core candidate |
| `sona-native-0.15.6-linux-aarch64-musl.tar.gz` | Linux ARM64 Native Core candidate |
| `sona-native-0.15.6-macos-x86_64.tar.gz` | macOS Intel Native Core candidate |
| `sona-native-0.15.6-macos-aarch64.tar.gz` | macOS Apple Silicon Native Core candidate |
| `sona-0.15.6-platform-test-kit.zip` | Cross-platform artifact verifier |

Artifact names alone are not compatibility evidence. Linux and macOS archives
must be produced and exercised by their matching runners before publication.
Android and iOS remain compile-only experiments, not supported installable
Native Core targets.

## Compatibility and known limits

- Python remains the broad compatibility engine; Native Core remains bounded.
- Proof Mode receipt-producing execution is Native-only and rejects fallback.
- Native HTTP remains unavailable with `SONA-HTTP-005`.
- Process and environment capabilities are not granted by Native Proof Mode.
- The package manager remains local-path only.
- The LSP still does not promise cross-file rename/references or formatting.
- Sona Guide is deterministic and offline; optional AI systems remain outside
  the Guide and Proof Mode verification chain.

## Documentation

- [Sona Guide](docs/guides/sona-guide.md)
- [Learn while you build](docs/guides/learning-and-examples.md)
- [Native command selection](docs/guides/native-command-selection.md)
- [Get Started with Proof Mode](docs/getting-started/README.md)
- [Proof Mode Guide](docs/guides/proof-mode.md)
- [Guardian Guide](docs/guides/guardian.md)
- [Using Proof Mode and Guardian Together](docs/guides/proof-and-guardian.md)
- [Proof Mode specification](docs/spec/proof/README.md)
- [Platform installation and testing](docs/guides/platform-installation-and-testing.md)
- [0.15.6 acceptance audit](docs/release/0.15.6-acceptance-audit.md)
- [0.15.6 finalization checklist](docs/release/0.15.6-finalization-checklist.md)
- [0.15.6 implementation report](docs/release/0.15.6-implementation-report.md)
