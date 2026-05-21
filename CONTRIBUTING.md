# Contributing to Sona

Thanks for helping improve Sona. Keep changes focused, documented, and aligned
with the current `0.14.0` developer experience.

## Setup

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

On Windows PowerShell, activate the environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

## Branches

- Use `main` for normal pull requests.
- Keep pull requests small enough to review.
- Do not commit local build output, virtual environments, coverage data, or
  one-off test files.

## Validation

Before opening a pull request, run the checks that match your change:

```bash
python -m sona --version
python -m sona --help
python tools/run_examples.py
```

For CLI changes, also verify local file execution:

```bash
echo 'print("Hello, Sona!")' > hello.sona
python -m sona hello.sona
```

Windows PowerShell:

```powershell
'print("Hello, Sona!")' | Out-File -Encoding utf8 hello.sona
python -m sona hello.sona
```

## Documentation

- Keep README and Quickstart examples based on local files.
- Put source-checkout-only examples in the `examples/` section.
- Do not publish planning notes, implementation journals, or local validation
  reports as public documentation.

## Pull Requests

Include:

- What changed.
- Why it changed.
- What validation you ran.
- Any known limitations or follow-up work.

## Commit Style

Prefer short conventional prefixes:

- `feat:`
- `fix:`
- `docs:`
- `chore:`
- `refactor:`

## License

By contributing, you agree that your contribution is licensed under the MIT
license used by this repository.
