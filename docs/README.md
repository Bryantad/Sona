# Sona Documentation

This folder contains the current user-facing documentation for Sona `0.15.5`.
Historical planning notes, implementation journals, test reports, and retired
feature drafts are intentionally not part of the published branch structure.

## Start Here

- [Get Started with Proof Mode](getting-started/README.md)
- [Quickstart](QUICKSTART.md)
- [Language Reference](LANGUAGE_REFERENCE.md)
- [Standard Library Reference](STDLIB_REFERENCE.md)
- [Proof Mode Guide](guides/proof-mode.md)
- [Guardian Guide](guides/guardian.md)
- [Using Proof Mode and Guardian Together](guides/proof-and-guardian.md)
- [Platform Installation and Testing](guides/platform-installation-and-testing.md)
- [Proof Mode Technical Reference](reference/native-proof-mode.md)
- [0.15.5 Standard Library Catalog](reference/stdlib/README.md)
- [Accessibility Reference](ACCESSIBILITY_REFERENCE.md)
- [Guardian Reference](GUARDIAN_REFERENCE.md)
- [Diagnostics Guide](errors/v0.14-diagnostics.md)
- [Language Server Support](devex/LSP_ROADMAP.md)
- [Package Manifest](packages/manifest.md)

## Roadmaps

Sona `0.15.5` keeps Python as the compatibility engine and ships Native Core as
a bounded preview. LLVM code generation, self-hosting, package publishing,
cross-file LSP indexing, formatter support, debugger support, and benchmark
expansion remain staged roadmap items, not completed `0.15.5` features.

- [Native Independence](roadmap/SONA_NATIVE_INDEPENDENCE.md)
- [Compiler Architecture](compiler/ARCHITECTURE.md)
- [LLVM Backend Plan](compiler/LLVM_BACKEND_PLAN.md)
- [Self-Hosting Plan](compiler/SELF_HOSTING_PLAN.md)
- [Runtime Independence Plan](compiler/RUNTIME_INDEPENDENCE_PLAN.md)
- [Package Manager Roadmap](spm/SONA_PACKAGE_MANAGER_ROADMAP.md)
- [Trusted Workflow Examples](../examples/trusted-workflows/README.md)
- [Deployment Contract Investigation](plans/0.15.5-deployment-contract.md)
- [Proof Mode Assurance Levels](spec/proof/assurance.md)
- [0.15.5 Trust Claims Audit](plans/0.15.5-trust-claims-audit.md)
- [0.15.5 Runtime Identity Review](plans/0.15.5-runtime-identity-review.md)
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
