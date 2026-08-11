# Platform Installation and Testing for Sona 0.15.4

Sona 0.15.4 uses one portable Python wheel, one Python source distribution,
and one VSIX across supported desktop operating systems. Native Core is
different: every operating system and CPU architecture receives its own
host-built, host-executed archive.

Do not rename a Windows executable or an unexecuted cross-compile and describe
it as Linux or macOS support. A Native Core release claim requires a green
build, dependency inspection, ordinary run, and Native Proof receipt on the
matching host.

## Desktop release matrix

| Operating system | Architecture | Python CLI and Guardian | Native Core artifact |
| --- | --- | --- | --- |
| Windows | x86-64 | Python 3.11 and 3.12 | `sona-native-0.15.4-windows-x86_64.zip` |
| Linux | x86-64 | Python 3.11 and 3.12 | `sona-native-0.15.4-linux-x86_64-musl.tar.gz` |
| Linux | ARM64 | Python 3.11 and 3.12 | `sona-native-0.15.4-linux-aarch64-musl.tar.gz` |
| macOS | Intel x86-64 | Python 3.11 and 3.12 | `sona-native-0.15.4-macos-x86_64.tar.gz` |
| macOS | Apple Silicon ARM64 | Python 3.11 and 3.12 | `sona-native-0.15.4-macos-aarch64.tar.gz` |

The Linux artifacts use static musl linking. The two macOS artifacts are
architecture-specific rather than a single universal binary, so users can
verify exactly which executable they received.

These names describe the intended 0.15.4 release matrix. Attach an artifact to
a GitHub Release only after the cross-platform workflow passes from the final
release commit. A prepared filename is not certification evidence.

## Portable artifacts

The same copies of these files are tested on every desktop target:

| Artifact | Purpose |
| --- | --- |
| `sona_lang-0.15.4-py3-none-any.whl` | Python-compatible CLI, Guardian, LSP server, and compatibility runtime |
| `sona_lang-0.15.4.tar.gz` | Python source distribution |
| `sona-ai-native-programming-0.15.4.vsix` | Desktop VS Code extension |
| `sona-0.15.4-platform-test-kit.zip` | Standard-library-only verifier and instructions |
| `sona-0.15.4-release-manifest.json` | Source commit and host-tested platform matrix |
| `SHA256SUMS.txt` | SHA-256 authority for the assembled release candidate |

The VSIX is portable JavaScript, but its Run, Guardian, and intelligence
features still depend on a compatible local `sona` installation. Browser-only
VS Code variants and mobile code-server installations are not certified by the
desktop VSIX matrix.

## Verify checksums first

Linux:

```bash
sha256sum --check SHA256SUMS.txt
```

macOS:

```bash
shasum -a 256 --check SHA256SUMS.txt
```

Windows PowerShell users can compare `Get-FileHash -Algorithm SHA256` output
with `SHA256SUMS.txt`.

## Linux installation and complete test

Use Python 3.11 or 3.12. Do not bypass Sona's `<3.13` package bound.

```bash
python3 --version
python3 -m venv .sona-0154-venv
source .sona-0154-venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ./sona_lang-0.15.4-py3-none-any.whl
sona --version
```

Extract the archive matching `uname -m`:

```bash
uname -m
tar -xzf sona-native-0.15.4-linux-x86_64-musl.tar.gz
chmod 755 ./sona
./sona --version
```

For ARM64, substitute
`sona-native-0.15.4-linux-aarch64-musl.tar.gz`.

Install the VSIX when desktop VS Code is available:

```bash
code --install-extension ./sona-ai-native-programming-0.15.4.vsix
```

Run the complete Python, Guardian, Native Proof, attestation, and deterministic
review test:

```bash
python -m zipfile -e sona-0.15.4-platform-test-kit.zip ./sona-test-kit
python ./sona-test-kit/sona-0.15.4-platform-test-kit/verify.py verify \
  --wheel ./sona_lang-0.15.4-py3-none-any.whl \
  --sdist ./sona_lang-0.15.4.tar.gz \
  --vsix ./sona-ai-native-programming-0.15.4.vsix \
  --native-archive ./sona-native-0.15.4-linux-x86_64-musl.tar.gz \
  --report ./sona-linux-verification.json
```

Use the ARM64 archive name on an ARM64 machine. The verifier rejects an archive
whose declared platform or architecture does not match the current host.

## macOS installation and complete test

Create a Python 3.11 or 3.12 environment and install the same wheel:

```bash
python3 --version
python3 -m venv .sona-0154-venv
source .sona-0154-venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ./sona_lang-0.15.4-py3-none-any.whl
sona --version
```

Choose the Native Core archive using `uname -m`:

```bash
uname -m
tar -xzf sona-native-0.15.4-macos-aarch64.tar.gz
chmod 755 ./sona
./sona --version
```

Intel Macs use `sona-native-0.15.4-macos-x86_64.tar.gz`.

The CI-built macOS preview artifacts are unsigned unless the release process
adds Apple Developer ID signing and notarization. Check the SHA-256 manifest
before testing. Do not present an unsigned build as Gatekeeper-ready production
distribution. Signing and notarization are separate publication gates.

Install the VSIX and run the same verifier command shown for Linux, replacing
the Native Core archive with the correct macOS filename.

## Windows test-kit command

After installing the wheel and extracting the Native Core ZIP, run:

```powershell
Expand-Archive .\sona-0.15.4-platform-test-kit.zip -DestinationPath .\sona-test-kit

python .\sona-test-kit\sona-0.15.4-platform-test-kit\verify.py verify `
  --wheel .\sona_lang-0.15.4-py3-none-any.whl `
  --sdist .\sona_lang-0.15.4.tar.gz `
  --vsix .\sona-ai-native-programming-0.15.4.vsix `
  --native-archive .\sona-native-0.15.4-windows-x86_64.zip `
  --report .\sona-windows-verification.json
```

The verifier extracts Native Core into a temporary directory; it does not
replace an installed executable.

## What a passing report establishes

The generated `sona-*-verification.json` report records:

- host operating system, CPU architecture, and Python version;
- exact wheel, source distribution, VSIX, and Native archive hashes;
- Python CLI syntax and execution success;
- Guardian initialization and clean-baseline verification;
- Native Core syntax, execution, and schema-1 Proof receipt success;
- Guardian-bound receipt verification and local attestation; and
- deterministic governed AI review plus local attestation history.

It remains local test evidence. It is not code signing, notarization, remote
attestation, a trusted timestamp, or hardware-backed identity.

## Android

Android is experimental in 0.15.4, not a supported Native Core release target.

The least misleading evaluation path is a Termux-like environment with Python
3.11 or 3.12. If the available Python is 3.13 or newer, stop rather than using
`--ignore-requires-python`.

After installing the wheel, run the portable Python and Guardian subset:

```bash
python -m zipfile -e sona-0.15.4-platform-test-kit.zip ./sona-test-kit
python ./sona-test-kit/sona-0.15.4-platform-test-kit/verify.py verify \
  --python-only \
  --wheel ./sona_lang-0.15.4-py3-none-any.whl \
  --report ./sona-android-python-verification.json
```

The Linux ARM64 musl archive is not automatically an Android artifact. Android
uses different userspace, application sandboxing, and distribution rules. Do
not publish or label that Linux archive as Android-compatible without an
Android-device execution gate.

The release workflow compile-checks the Rust workspace for
`aarch64-linux-android`; that proves source compilation only, not installation,
execution, Guardian integration, or mobile support.

## iOS and iPadOS

Sona 0.15.4 does not provide an installable iOS CLI, `.ipa`, or App Store
package. iOS requires an application wrapper, code signing, provisioning,
sandbox-aware filesystem design, and device or simulator tests. A normal
desktop `pip install`, VSIX, or terminal binary distribution is not an honest
iOS support path.

The release workflow compile-checks the Rust workspace for
`aarch64-apple-ios`. This is useful portability evidence, but it does not prove
that the current CLI can run as an iOS application. A future mobile release
should expose Native Core as an embeddable library behind a signed Xcode app
instead of trying to ship the desktop CLI unchanged.

## GitHub Actions release gate

`.github/workflows/release-platforms-0154.yml` builds without publishing. It:

1. builds and inspects the wheel, sdist, and VSIX once;
2. builds each Native Core archive on its matching host;
3. runs Python 3.11 and 3.12 verification on all five desktop targets;
4. reports non-blocking Android and iOS compile-only experiments with explicit
   experimental labels;
5. assembles one exact candidate with a release manifest and checksums; and
6. uploads workflow artifacts for review without creating a tag or release.

Run it from the final commit. Download the assembled candidate, review every
platform report, and attach only the files covered by its `SHA256SUMS.txt`.
