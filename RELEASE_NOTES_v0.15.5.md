# Sona 0.15.5 — Trusted Developer Workflow

Sona 0.15.5 turns the trust foundations introduced in 0.15.4 into a more
usable developer workflow. The release adds one shared receipt verifier,
Guardian policy hardening, practical onboarding, stabilized editor support,
local package-manager safeguards, and executable trusted-workflow examples.

No Sona syntax change is introduced. Existing valid schema-1 receipts,
including frozen 0.15.4 receipts, remain supported.

## Highlights

### Verify and inspect Proof Mode receipts

The Python-hosted CLI now provides:

```bash
sona proof verify receipt.sproof
sona proof inspect receipt.sproof
sona proof verify receipt.sproof --json
sona proof inspect receipt.sproof --json
```

Verification checks the schema identifier and version, exact canonical JSON
encoding, required fields, receipt self-hash, runtime and engine identity,
fallback status, capabilities, effects, execution facts, and optional Guardian
binding. Invalid or malformed receipts fail closed with stable diagnostics.

New 0.15.5 Native receipts may also record the SHA-256 identity and byte size
of the executable that produced them, plus an optional build-supplied Git
revision. Those values help correlate evidence; they are not signer identity
or authenticated provenance.

### Guardian workflow hardening

Guardian remains local and project-scoped. The supported workflow is easier to
initialize, check, and explain:

```bash
sona guardian init --project-root .
sona guardian check --project-root .
sona guardian explain --project-root .
```

Guardian policy decisions feed explicit Native capabilities; Native execution
then records the observed host-facing effects in the receipt. Guardian can
verify the local policy/baseline binding and record a local audit result. AI
review remains advisory and outside receipt generation and verification.

### Proof Mode Explorer for VS Code

The `0.15.5` extension adds a CLI-backed Proof Mode Explorer. It can run the
active Sona file with Proof Mode, verify or inspect a receipt through the
shared Sona CLI, open the receipt, and request Guardian explanation from a
trusted workspace. The extension does not reimplement verification in
TypeScript.

### Stabilized language-server foundation

The supported LSP surface now covers canonical diagnostics, local and standard
library completion, known-symbol hover, current-document definition, and
top-level document symbols. Rename, references, cross-file indexing, LSP
formatting, and debugging remain deferred.

### Safer local package workflows

`sona pkg` and the compatible `spm` command now share the same hardened local
transaction engine. SPM validates dependency names and paths, confines writes
to the project, rejects symlink traversal, verifies integrity, stages the full
dependency set, commits atomically, and restores prior state on failure. This
release does not add a registry, downloads, publishing, or package signing.

### Executable trusted-workflow examples

Four source-checkout examples demonstrate bounded workflows:

- AI action evidence, where an external proposal is treated as untrusted input;
- an auditable integer-cent calculation;
- a loopback service API through the Python compatibility runtime; and
- local deployment evidence with Guardian policy and artifact hashing.

The service example deliberately does not produce a Native Proof Mode receipt,
because Native HTTP is still unavailable and no Python fallback is claimed.

## Assurance boundary

Proof Mode provides deterministic receipt integrity checking for the evidence
fields emitted by Sona. It does not provide:

- signer or operator identity;
- a trusted timestamp;
- a trusted execution environment or operating-system integrity proof;
- remote attestation;
- protection against replacing and re-hashing an entire receipt; or
- a claim that Python-compatible and Native executions are semantically equal.

Guardian's `attest` command records a local audit conclusion. It is not a
cryptographic signature, PKI assertion, or remote attestation. See
[`docs/spec/proof/assurance.md`](docs/spec/proof/assurance.md) and
[`docs/spec/proof/threat-model.md`](docs/spec/proof/threat-model.md).

## Installation

Python 3.11 or 3.12:

```bash
python -m pip install sona_lang-0.15.5-py3-none-any.whl
sona --version
```

VS Code:

```bash
code --install-extension sona-ai-native-programming-0.15.5.vsix
```

Proof Mode execution also requires the Native Core archive matching the host.
Verify every downloaded artifact against `SHA256SUMS.txt` before installation.

## Release artifacts

| Artifact | Purpose |
| --- | --- |
| `sona_lang-0.15.5-py3-none-any.whl` | Python-compatible CLI, Guardian, LSP, SPM, and runtime |
| `sona_lang-0.15.5.tar.gz` | Python source distribution |
| `sona-ai-native-programming-0.15.5.vsix` | VS Code extension |
| `sona-native-0.15.5-windows-x86_64.zip` | Windows x86-64 Native Core |
| `sona-native-0.15.5-linux-x86_64-musl.tar.gz` | Linux x86-64 Native Core candidate |
| `sona-native-0.15.5-linux-aarch64-musl.tar.gz` | Linux ARM64 Native Core candidate |
| `sona-native-0.15.5-macos-x86_64.tar.gz` | macOS Intel Native Core candidate |
| `sona-native-0.15.5-macos-aarch64.tar.gz` | macOS Apple Silicon Native Core candidate |
| `sona-0.15.5-platform-test-kit.zip` | Cross-platform artifact verifier |

Windows artifacts can be built and tested locally. Linux and macOS archives
must be produced and exercised by their matching GitHub Actions runners before
publication; artifact names alone are not compatibility evidence. Android and
iOS remain experiments, not supported installable Native Core targets.

## Compatibility and known limits

- Python remains the broad compatibility engine; Native Core remains bounded.
- Proof Mode receipt-producing execution is Native-only and rejects fallback.
- Native HTTP remains unavailable with `SONA-HTTP-005`.
- Process and environment capabilities are not granted by Native Proof Mode.
- The package manager remains local-path only.
- The LSP does not yet provide cross-file rename/references or formatting.
- No signatures, PKI, trusted timestamping, remote attestation, cloud trust
  service, or package registry is included.

## Documentation

- [Get Started with Proof Mode](docs/getting-started/README.md)
- [Proof Mode Guide](docs/guides/proof-mode.md)
- [Guardian Guide](docs/guides/guardian.md)
- [Using Proof Mode and Guardian Together](docs/guides/proof-and-guardian.md)
- [Proof Mode specification](docs/spec/proof/README.md)
- [Platform installation and testing](docs/guides/platform-installation-and-testing.md)
- [0.15.5 implementation report](docs/release/0.15.5-implementation-report.md)
