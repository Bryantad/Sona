# Sona

Sona is a Python-hosted programming language focused on clear CLI behavior,
deterministic examples, and developer-friendly diagnostics.

Current release: `0.14.0`

## Install

Sona requires Python 3.11 or newer.

```bash
python -m pip install sona-lang
```

Confirm the install:

```bash
sona --version
```

Expected shape:

```text
Sona 0.14.0
```

## First Run

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

## CLI

```bash
sona --help
sona run hello.sona
sona hello.sona
```

`sona run <file.sona>` and `sona <file.sona>` are both supported for local
files. Repository examples are available only from a source checkout.

## Documentation

- [Quickstart](docs/QUICKSTART.md)
- [Language Reference](docs/LANGUAGE_REFERENCE.md)
- [Standard Library Reference](docs/STDLIB_REFERENCE.md)
- [Diagnostics Guide](docs/errors/v0.14-diagnostics.md)
- [Package Manifest](docs/packages/manifest.md)

## Source Checkout Examples

Official examples are kept in the repository for documentation and release
validation. They are not required to ship inside the installed Python package.

```bash
python tools/run_examples.py
```

## VS Code

The main Sona VS Code extension lives in [`vscode-extension/`](vscode-extension/).
The Receipt Explorer companion extension lives in
[`extensions/sona-receipt-explorer/`](extensions/sona-receipt-explorer/).

## Package Scope

The published Python package is intentionally lean. Source-only docs, examples,
tests, extension sources, and local validation artifacts are excluded from the
wheel and sdist.

## License

MIT. See [LICENSE](LICENSE).
