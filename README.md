# Sona

Sona is an AI-native programming language and developer toolchain focused on
clear execution, readable diagnostics, deterministic examples, and cognitive
accessibility.

[![Source Version](https://img.shields.io/github/v/tag/Bryantad/Sona?label=source\&sort=semver)](https://github.com/Bryantad/Sona/tags)
[![CI](https://github.com/Bryantad/Sona/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/Bryantad/Sona/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Package](https://img.shields.io/badge/package-sona--lang-blue)](https://pypi.org/project/sona-lang/)
[![License](https://img.shields.io/github/license/Bryantad/Sona)](LICENSE)

[![VS Code Marketplace](https://img.shields.io/visual-studio-marketplace/v/Waycoreinc.sona-receipt-explorer?label=VS%20Code%20Marketplace\&logo=visualstudiocode)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-receipt-explorer)
[![VS Code Installs](https://img.shields.io/visual-studio-marketplace/i/Waycoreinc.sona-receipt-explorer?label=VS%20Code%20installs\&logo=visualstudiocode)](https://marketplace.visualstudio.com/items?itemName=Waycoreinc.sona-receipt-explorer)
[![YouTube](https://img.shields.io/badge/YouTube-Sona-red?logo=youtube&logoColor=white)](https://www.youtube.com/@LearnSonaLang)
[![X](https://img.shields.io/badge/X-@YOUR_HANDLE-black?logo=x\&logoColor=white)](https://x.com/YOUR_HANDLE)
[![GitHub Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-Sponsor-ea4aaa?logo=githubsponsors\&logoColor=white)](https://github.com/sponsors/Bryantad)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support-ff5e5b?logo=kofi\&logoColor=white)](https://ko-fi.com/YOUR_HANDLE)

Current source release: `0.15.1`

## What Sona Provides

* A Python-hosted runtime and CLI for `.sona` programs.
* A stable first-run path for new developers.
* Clear user-facing diagnostics with actionable hints.
* A source-validated official example suite.
* Standard library documentation for stable user-facing modules.
* Cognitive accessibility references for supported developer workflows.
* Guardian runtime documentation for local resilience and release trust surfaces.

## Install

Sona requires Python 3.11 or newer.

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
Sona 0.15.1
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

* [Quickstart](docs/QUICKSTART.md)
* [Language Reference](docs/LANGUAGE_REFERENCE.md)
* [Standard Library Reference](docs/STDLIB_REFERENCE.md)
* [Accessibility Reference](docs/ACCESSIBILITY_REFERENCE.md)
* [Guardian Reference](docs/GUARDIAN_REFERENCE.md)
* [Diagnostics Guide](docs/errors/v0.14-diagnostics.md)
* [Package Manifest](docs/packages/manifest.md)
* [Native Independence Roadmap](docs/roadmap/SONA_NATIVE_INDEPENDENCE.md)
* [Release Notes](RELEASE_NOTES_v0.15.1.md)

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
