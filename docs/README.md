# Sona Documentation

This folder contains the current user-facing documentation for Sona `0.15.1`.
Historical planning notes, implementation journals, test reports, and retired
feature drafts are intentionally not part of the published branch structure.

## Start Here

- [Quickstart](QUICKSTART.md)
- [Language Reference](LANGUAGE_REFERENCE.md)
- [Standard Library Reference](STDLIB_REFERENCE.md)
- [Accessibility Reference](ACCESSIBILITY_REFERENCE.md)
- [Guardian Reference](GUARDIAN_REFERENCE.md)
- [Diagnostics Guide](errors/v0.14-diagnostics.md)
- [Package Manifest](packages/manifest.md)

## Roadmaps

Sona `0.15.1` still uses the Python-backed runtime. Native compiler
independence, LLVM code generation, self-hosting, package publishing, full LSP
completion, formatter support, debugger support, and benchmark expansion are
staged roadmap items, not completed `0.15.1` features.

- [Native Independence](roadmap/SONA_NATIVE_INDEPENDENCE.md)
- [Compiler Architecture](compiler/ARCHITECTURE.md)
- [LLVM Backend Plan](compiler/LLVM_BACKEND_PLAN.md)
- [Self-Hosting Plan](compiler/SELF_HOSTING_PLAN.md)
- [Runtime Independence Plan](compiler/RUNTIME_INDEPENDENCE_PLAN.md)
- [Package Manager Roadmap](spm/SONA_PACKAGE_MANAGER_ROADMAP.md)
- [LSP Roadmap](devex/LSP_ROADMAP.md)
- [Formatter Roadmap](devex/FORMATTER_ROADMAP.md)
- [Debugger Roadmap](devex/DEBUGGER_ROADMAP.md)
- [Benchmarking Roadmap](devex/BENCHMARKING_ROADMAP.md)

## Error Documentation

- [v0.14 Diagnostics Guide](errors/v0.14-diagnostics.md) is the current
  runtime-backed diagnostics contract.
- [v0.10 Error Behavior](errors/v0.10-errors.md) is historical context only.

## Documentation Rules

- README and Quickstart examples must use local files, not repository-only paths.
- Repository examples are source-checkout validation assets only.
- Planning files, test reports, and implementation notes stay local unless they
  become stable public documentation.
