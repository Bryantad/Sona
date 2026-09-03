# Sona

Sona is a simple programming language designed for software that can provide
evidence of what it did.

**Proof Mode** records privacy-conscious execution evidence such as program
identity, capabilities, observable effects, runtime identity, output identity,
and execution result. **Guardian** provides local policy around what trusted
automation is allowed to do and can bind that evidence to a reviewed project
baseline.

[![Source Version](https://img.shields.io/github/v/tag/Bryantad/Sona?label=source\&sort=semver)](https://github.com/Bryantad/Sona/tags)
[![CI](https://github.com/Bryantad/Sona/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Bryantad/Sona/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Package](https://img.shields.io/badge/package-sona--lang-blue)](https://pypi.org/project/sona-lang/)
[![License](https://img.shields.io/github/license/Bryantad/Sona)](LICENSE)
[![VS Code Marketplace](https://img.shields.io/visual-studio-marketplace/v/Waycoreinc.sona-ai-native-programming?label=VS%20Code%20Marketplace&logo=visualstudiocode)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)
[![VS Code Installs](https://img.shields.io/visual-studio-marketplace/i/Waycoreinc.sona-ai-native-programming?label=VS%20Code%20installs&logo=visualstudiocode)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-ai-native-programming)
[![YouTube](https://img.shields.io/badge/YouTube-Sona-red?logo=youtube&logoColor=white)](https://www.youtube.com/@LearnSonaLang)
[![GitHub Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-Sponsor-ea4aaa?logo=githubsponsors\&logoColor=white)](https://github.com/sponsors/Bryantad)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support-ff5e5b?logo=kofi\&logoColor=white)](https://ko-fi.com/YOUR_HANDLE)

Current release: `0.15.5`

## Why Sona?

Most programs give you a result. Sona can also give you a portable receipt that
describes the exact Native Core program that ran, the capabilities it received,
the host-facing effects Sona observed, and whether execution succeeded. The
receipt omits source text, output bodies, raw paths, credentials, and
environment values by default.

That makes Sona useful when a local automation, build step, calculation, or
AI-assisted workflow needs a reviewable record instead of only a log line.

## Why not just Python?

Python remains an excellent general-purpose language, and Sona includes a
Python-hosted compatibility runtime for broad day-to-day use. Sona's distinct
focus is an integrated language workflow for explicit capabilities, Native
Core execution, Proof Mode receipts, and Guardian policy.

Proof Mode never silently claims that a Python-compatible run was Native. In
schema 1, receipt-producing execution is Native-only, records no Python or
fallback participation, and fails closed when Native Core is unavailable.

## What is Proof Mode?

Run a supported `.sona` program with Native Core and a new receipt path:

```bash
sona proof hello.sona --receipt hello.sproof --engine native
sona proof verify hello.sproof
sona proof inspect hello.sproof
```

The receipt's deterministic self-hash supports integrity and consistency
checking. It is not a digital signature, signer identity, trusted timestamp,
hardware proof, or remote attestation. Guardian can add a local policy and
baseline binding; it does not turn the receipt into authenticated evidence.

## What can I build today?

* Small command-line programs, calculations, and file-processing automation.
* Guardian-controlled Native workflows with explicit filesystem capabilities.
* Local AI-assisted workflows where the model remains outside the verification
  chain and only instrumented Native actions become Proof Mode evidence.
* Python-compatible applications using the broader standard library, including
  HTTP, while keeping those runs distinct from Native Proof Mode.
* Editor workflows with diagnostics, completion, navigation, and a CLI-backed
  Proof Mode Explorer in the Sona VS Code extension.

Native HTTP remains unavailable, so Sona does not claim verified network
effects for a successful HTTP operation in this release.

## Try Sona quickly

Sona requires Python 3.11 or 3.12:

```bash
python -m pip install sona-lang
sona --version
```

Create and run a first program:

```bash
echo 'print("Hello, Sona!")' > hello.sona
sona run hello.sona
```

On Windows PowerShell:

```powershell
'print("Hello, Sona!")' | Set-Content -Encoding ascii hello.sona
sona run .\hello.sona
```

For a tested ten-minute path through Native Core, receipt verification,
Guardian policy, and an intentional capability denial, follow
[Get Started with Proof Mode](docs/getting-started/README.md).

## Current capabilities

* A Python-hosted compatibility runtime and CLI for `.sona` programs.
* A stable first-run path for new developers.
* Clear user-facing diagnostics with actionable hints.
* A source-validated official example suite.
* A manifest-backed standard library with canonical filesystem, HTTP, JSON,
  date/time, random, stream, and input contracts.
* Explicit runtime capabilities for safe Python-compatible runs and Native
  Core filesystem/network access.
* Opt-in Proof Mode receipts that bind to a Guardian-tracked baseline and
  gain explicit local verification, audit attestation, and governed advisory
  AI review for release workflows.
* Cognitive accessibility references for supported developer workflows.
* Guardian runtime documentation for local resilience and release trust surfaces.

## Install details

Sona requires Python 3.11 or 3.12.

Install the published Python package:

```bash
python -m pip install sona-lang
```

Confirm the install:

```bash
sona --version
```

Expected output shape:

```text
Sona 0.15.5
```

> Note: the source repository may be ahead of the latest published PyPI package.
> For the newest source release, install from a source checkout.

## First Run

The README does not assume access to repository examples. Create a local file
first, then run it.

Bash or macOS/Linux shell:

```bash
echo 'print("Hello, Sona!")' > hello.sona
sona hello.sona
```

Windows PowerShell:

```powershell
'print("Hello, Sona!")' | Out-File -Encoding utf8 hello.sona
sona hello.sona
```

Expected output:

```text
Hello, Sona!
```

## CLI Basics

```bash
sona --help
sona run hello.sona
sona hello.sona
```

Both `sona run <file.sona>` and `sona <file.sona>` are supported for local files.

## Documentation

* [Get Started with Proof Mode](docs/getting-started/README.md)
* [Quickstart](docs/QUICKSTART.md)
* [Language Reference](docs/LANGUAGE_REFERENCE.md)
* [Standard Library Reference](docs/STDLIB_REFERENCE.md)
* [Proof Mode Guide](docs/guides/proof-mode.md)
* [Guardian Guide](docs/guides/guardian.md)
* [Using Proof Mode and Guardian Together](docs/guides/proof-and-guardian.md)
* [Platform Installation and Testing](docs/guides/platform-installation-and-testing.md)
* [0.15.5 Standard Library Catalog](docs/reference/stdlib/README.md)
* [Accessibility Reference](docs/ACCESSIBILITY_REFERENCE.md)
* [Guardian Reference](docs/GUARDIAN_REFERENCE.md)
* [Diagnostics Guide](docs/errors/v0.14-diagnostics.md)
* [Package Manifest](docs/packages/manifest.md)
* [Native Independence Roadmap](docs/roadmap/SONA_NATIVE_INDEPENDENCE.md)
* [0.15.5 Release Notes](RELEASE_NOTES_v0.15.5.md)

## Official Examples

Official examples are part of the source repository validation surface. They are
not required to exist in installed Python packages.

From a source checkout:

```bash
python tools/run_examples.py
sona run examples/hello.sona
```

## VS Code

Sona has VS Code ecosystem support through the Sona editor tooling and companion
extensions.

* The main Sona VS Code extension provides syntax highlighting, command palette
  actions, and editor workflow support for `.sona` and `.smod` files.
* The [Sona Receipt Explorer](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-receipt-explorer)
  visualizes and compares Sona execution receipt files.

## Repository Layout

```text
sona/                         Core runtime, CLI, parser, and packaged stdlib
stdlib/                       Source .smod modules
docs/                         Current user-facing documentation
examples/                     Official source-checkout examples
tools/run_examples.py         Source-checkout example validator
.github/workflows/ci.yml      Continuous integration workflow
.github/workflows/release-platforms-0155.yml
                              Cross-platform release-candidate workflow
vscode-extension/             Main Sona VS Code extension
extensions/sona-receipt-explorer/
                              Receipt Explorer VS Code extension
```

## Package Scope

The Python package is intentionally lean. Docs, examples, tests, extension
sources, local reports, and build artifacts are source-repository materials and
are excluded from release wheels and sdists.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Keep pull requests focused, document
runtime-visible behavior, and do not commit local test files, temporary build
output, or planning notes.

## License

Sona is released under the MIT license. See [LICENSE](LICENSE).
