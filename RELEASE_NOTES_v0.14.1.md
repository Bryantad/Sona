# Sona v0.14.1 - Sona-Native Stdlib Foundation

Sona `0.14.1` moves the public standard library foundation toward
Sona-authored `.smod` modules and adds a release-hardening gate for Python
artifacts.

## Highlights

- Added manifest metadata for stdlib module source and stability.
- Added Sona-authored foundation modules for queues, stacks, sorting, search,
  statistics, matrices, graphs, and permissions.
- Added Sona-authored wrappers for hashing, random values, UUIDs, secrets,
  passwords, JWT-style tokens, and crypto helpers over a minimal private
  intrinsic set.
- Kept private intrinsics and `native_bridge` out of normal user-facing module
  listings and imports.
- Removed eager interpreter construction at import time and reduced stdlib
  startup preload to foundation/stable modules.
- Added release hardening for wheel, sdist, clean installed-package smoke
  checks, archive inspection, and artifact hashes.

## Sona-Native Stdlib Foundation

Public foundation modules now ship as `.smod` source where Sona can implement
the behavior directly:

- `queue`
- `stack`
- `sort`
- `search`
- `statistics`
- `matrix`
- `graph`
- `permissions`

Public wrappers over private host intrinsics now also ship as `.smod` modules:

- `hashing`
- `random`
- `uuid`
- `secrets`
- `password`
- `jwt`
- `crypto`

The private intrinsic surface is intentionally small and remains internal to
the runtime. Private intrinsics and `native_bridge` are excluded from normal
user imports, LSP-facing user module lists, stdlib probe user lists, and
build-info user module lists.

## Release Hardening

This release adds `scripts/release_hardening.ps1`, a separate packaging gate
that calls the existing fast release gate and then validates release artifacts.

The hardening gate checks:

- Python tests, CLI version, stdlib probe, build-info, and official examples.
- Wheel and sdist build output.
- Required stdlib runtime files in both Python artifacts.
- Forbidden repository-only material excluded from Python artifacts.
- Fresh wheel install in a temporary venv outside the repository source tree.
- Installed import resolution pointing into the temporary venv.
- Final SHA-256 hashes for the wheel and sdist.

## Validation

The release hardening pass completed with:

```text
python -m pytest -q tests
python -m sona --version
python -m sona probe stdlib
python -m sona build-info
python tools/run_examples.py
powershell -ExecutionPolicy Bypass -File scripts\release_hardening.ps1
python -m twine check --strict dist-pypi-0.14.1/*
```

Results:

- `pytest`: 15 passed.
- `sona --version`: `Sona 0.14.1`.
- `probe stdlib`: status `ok`.
- `tools/run_examples.py`: 9 examples passed.
- `twine check --strict`: passed for wheel and sdist.

## Artifacts

```text
Wheel:
  dist-pypi-0.14.1\sona_lang-0.14.1-py3-none-any.whl
  SHA-256: 88c38004aa38cb526069470b3bfb949b997543bfe9e413e8e2d13840170aca5c

Sdist:
  dist-pypi-0.14.1\sona_lang-0.14.1.tar.gz
  SHA-256: 6a6a35861cec95b153414f86a79609b186dadfe92ff7a7f2781cb1bd02eb712d

```

## Compatibility Notes

No parser, grammar, NativeBridge redesign, dependency addition, `.sona` stdlib
module path, public function removal, marketplace publishing automation, or
PyPI upload automation is included in this release.

`crypto.encrypt_simple` remains preview/legacy obfuscation only and is not
production encryption.
