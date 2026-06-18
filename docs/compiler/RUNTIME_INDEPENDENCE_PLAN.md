# Runtime Independence Plan

Sona `0.15.0` remains Python-backed. Runtime independence is a staged roadmap
that depends on correctness, packaging discipline, and clear host boundaries.

## Current Runtime Boundaries

- Python hosts parser, interpreter, module loading, and native backends.
- `.smod` modules can define public Sona-facing behavior.
- Manifest metadata controls discovery and hidden-module filtering.
- Guardian uses local filesystem state and Python-backed helpers.

## Independence Workstreams

- Define a stable runtime value model.
- Isolate host intrinsics behind narrow interfaces.
- Keep public APIs independent from Python module names.
- Validate clean installs outside the repository.
- Add native execution only when it can pass the same public behavior tests.

Runtime independence must not reduce safety, diagnostics, or local-first privacy
guarantees.
