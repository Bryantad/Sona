# Sona Documentation

This folder contains the current user-facing documentation for Sona `0.14.0`.
Historical planning notes, implementation journals, test reports, and retired
feature drafts are intentionally not part of the published branch structure.

## Start Here

- [Quickstart](QUICKSTART.md)
- [Language Reference](LANGUAGE_REFERENCE.md)
- [Standard Library Reference](STDLIB_REFERENCE.md)
- [Diagnostics Guide](errors/v0.14-diagnostics.md)
- [Package Manifest](packages/manifest.md)

## Error Documentation

- [v0.14 Diagnostics Guide](errors/v0.14-diagnostics.md) is the current
  runtime-backed diagnostics contract.
- [v0.10 Error Behavior](errors/v0.10-errors.md) is historical context only.

## Documentation Rules

- README and Quickstart examples must use local files, not repository-only paths.
- Repository examples are source-checkout validation assets only.
- Planning files, test reports, and implementation notes stay local unless they
  become stable public documentation.
