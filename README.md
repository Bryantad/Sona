# Sona

Sona is an AI-native programming language and developer toolchain focused on
clear execution, readable diagnostics, deterministic examples, and cognitive
accessibility.

[![Source Version](https://img.shields.io/github/v/tag/Bryantad/Sona?label=source&sort=semver)](https://github.com/Bryantad/Sona/tags)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Bryantad/Sona)](LICENSE)

Current release: `0.15.1`

## What Sona Provides

- A Python-hosted runtime and CLI for `.sona` programs.
- A stable first-run path for new developers.
- Clear user-facing diagnostics with actionable hints.
- A source-validated official example suite.
- Standard library documentation for the stable user-facing modules.

## Install

Sona requires Python 3.11 or newer.

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

Both `sona run <file.sona>` and `sona <file.sona>` are supported for local
files.

## Documentation

- [Quickstart](docs/QUICKSTART.md)
- [Language Reference](docs/LANGUAGE_REFERENCE.md)
- [Standard Library Reference](docs/STDLIB_REFERENCE.md)
- [Accessibility Reference](docs/ACCESSIBILITY_REFERENCE.md)
- [Guardian Reference](docs/GUARDIAN_REFERENCE.md)
- [Diagnostics Guide](docs/errors/v0.14-diagnostics.md)
- [Package Manifest](docs/packages/manifest.md)
- [Native Independence Roadmap](docs/roadmap/SONA_NATIVE_INDEPENDENCE.md)
- [Release Notes](RELEASE_NOTES_v0.15.1.md)

## Official Examples

Official examples are part of the source repository validation surface. They are
not required to exist in installed Python packages.

From a source checkout:

```bash
python tools/run_examples.py
sona run examples/hello.sona
```

## Repository Layout

```text
sona/                         Core runtime, CLI, parser, and packaged stdlib
stdlib/                       Source .smod modules
docs/                         Current user-facing documentation
examples/                     Official source-checkout examples
tools/run_examples.py         Source-checkout example validator
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
