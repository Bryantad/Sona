# Sona

Sona is an AI-native programming language with a focus on cognitive
accessibility, deterministic tooling, and clear developer feedback.

## Sona 0.14.0 Developer Quick Start

Sona `0.14.0` focuses on developer usability: install, run, docs, examples,
errors, packaging, and VS Code extension stability.

Install the CLI:

```bash
pip install sona-lang
sona --version
sona --help
```

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

## Documentation

- [Quickstart](docs/QUICKSTART.md)
- [Language Reference](docs/LANGUAGE_REFERENCE.md)
- [Stdlib Reference](docs/STDLIB_REFERENCE.md)
- [Diagnostics Guide](docs/errors/v0.14-diagnostics.md)
- [Official Examples](examples/README.md)

## Source-Checkout Examples

Official examples are validated from a source checkout. Installed packages do
not need to include repository examples.

Run one example from the repository:

```bash
sona run examples/hello.sona
```

Validate the official example suite:

```bash
python tools/run_examples.py
```

## CLI Behavior

- `sona --version` prints one line, for example `Sona 0.14.0`.
- `sona --help` shows commands and short examples.
- `sona <file.sona>` and `sona run <file.sona>` both execute a local file.
- CLI errors print to stderr and exit nonzero.
- Stack traces are hidden by default; use `--errors=trace` or `--errors=both`
  when debugging runtime internals.

## VS Code

The VS Code extension provides syntax highlighting, command palette actions,
and **Sona: Run Sona File** for `.sona` and `.smod` files. See
[`vscode-extension/README.md`](vscode-extension/README.md).

## Release Notes

- [Sona v0.14.0 release notes](RELEASE_NOTES_v0.14.0.md)
- [Sona v0.14.0 release checklist](docs/release-notes/v0.14.0_RELEASE_CHECKLIST.md)

## License

MIT License. See [LICENSE](LICENSE).
