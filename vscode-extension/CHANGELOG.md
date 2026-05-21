# Changelog

## 0.14.0

- Aligns the extension with Sona 0.14.0.
- Updates onboarding copy around the stable CLI flow: `sona --version`, `sona --help`, `sona run <file.sona>`, and `sona <file.sona>`.
- Removes normal-run parser initialization noise from CLI execution.
- Updates extension dependencies to resolve shipped VSIX security advisories.
- Keeps the existing Run Sona File command and syntax highlighting activation surface stable.
- Maintains VSIX package hygiene from the 0.13.1 cleanup line.

## 0.13.1

- Aligns the extension with Sona 0.13.1.
- Tightens VSIX ignore rules for local artifacts, caches, logs, and old inspection output.
- Keeps the 0.13.x runtime governance and native stdlib behavior unchanged.

## 0.13.0

- Aligns the extension with Sona 0.13.0.
- Persistent memory governance layer: policy enforcement, audit logging, and compliance reporting.
- Ships `stdlib/memory.smod` for persistent memory operations in `.sona` programs.
- Closes the stdlib native migration: all 19 release `.smod` modules use `runtime_backend = "smod"` with no `__native__` bridge calls in the stdlib surface.

## 0.12.0

- Aligns the extension with Sona 0.12.0.
- Runtime boundary cleanup: public model layer separated from advanced/internal kernels.
- Ships `stdlib/utils/convert.smod` — first nested `.smod` conversion helper.

## 0.11.1

- Aligns the extension with Sona 0.11.1.
- Fixes `when` subject evaluation, dead continue-path code, and ghost attribute checks.
- Adds `for a, b in value` destructuring support.
- Parser caching for faster startup.

## 0.11.0

- Aligns the extension with Sona 0.11.0 (absorbs v0.10.4 scope).
- Native `.smod` architecture completed: 18 modules with explicit metadata contracts.
- Trust-layer governance: receipt signing, redaction, export, chain verification, and replay contracts.
- New modules: `receipt.smod` and `emotion.smod`.

## 0.10.3

- Aligns the extension with Sona 0.10.3.
- Native `.smod` module milestone: `regex.smod`, `uuid.smod`, `hashing.smod`.
- Packaging includes `stdlib/*.smod` in release artifacts.

## 0.10.2

- Aligns the extension with Sona 0.10.2.
- Fixes `repeat while`/`repeat until`, multiline strings, and LSP outline positioning.
- Adds `string.template(...)` `.smod` support.

## 0.10.1

- Aligns with Sona 0.10.1 (execution receipts + stdlib expansions).
- Consolidated Cognitive Preview foundation and documentation reorganization.
- Adds real-world smoke coverage for CLI execution and receipts.
