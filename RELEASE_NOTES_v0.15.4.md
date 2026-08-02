# Sona 0.15.4 - Standard Library Cohesion and Runtime Capability

Sona 0.15.4 turns the existing standard-library surface into a reviewed
runtime contract. It preserves the Python-compatible language behavior and
the 0.15.3 Native Core preview while making common filesystem, data, network,
stream, input, random, string, date, and time work predictable.

## Standard-library contract

- `sona/stdlib/MANIFEST.json` is now the schema-2 authority for 146 preserved
  modules. It records signatures, compatibility dispositions, diagnostic
  behavior, and Python/Native/standalone support classifications.
- The certified foundation is `collection`, `date`, `fs`, `http`, `io`,
  `json`, `math`, `random`, `stdin`, `string`, and `time`.
- The generated catalog and module reference are derived from that manifest.
- Private `native_*` modules remain implementation details. Application code
  uses the public module names.

## Runtime capabilities

- Python-compatible normal runs retain filesystem and network access.
- `--safe` confines filesystem reads to the project root and denies secret
  reads, filesystem writes, and network access.
- Native Core remains console-only by default. Filesystem and network access
  require explicit `--allow-fs-read`, `--allow-fs-write`, and
  `--allow-network` flags.
- Native HTTP is importable but intentionally unavailable in 0.15.4. It emits
  the stable `SONA-HTTP-005` diagnostic instead of silently falling back.

## Canonical APIs and diagnostics

- `fs` now exposes the canonical UTF-8 text and path operations while keeping
  0.15.x aliases quiet and compatible.
- `http` provides bounded Python-compatible GET, POST, PUT, PATCH, and DELETE
  requests with structured responses, timeouts, redirects, headers, JSON
  bodies, response-size limits, and sanitized transport diagnostics.
- JSON output uses deterministic key ordering; random seeding is repeatable
  within each engine; stream output and console input have distinct modules.
- Host failures use stable `SONA-FS-*`, `SONA-HTTP-*`, `SONA-JSON-*`,
  `SONA-IO-*`, `SONA-TIME-*`, and `SONA-STDLIB-*` diagnostic families and
  carry the application call location.

## Native Core preview

Native Core includes a workspace-first host-module registry for the bounded
foundation. Collection and random remain honestly classified as `PARTIAL`,
and HTTP as `UNSUPPORTED`. The release does not claim full Python/Native
semantic parity or serialized instruction bytecode.

## Compatibility

- Valid 0.15.3 Python-compatible programs, implicit final-statement function
  values, cognitive runtime behavior, Guardian interfaces, and workspace
  module precedence are preserved.
- Existing public modules remain importable. Canonical aliases are quiet for
  the rest of the 0.15.x line.
- The tracked VS Code extension remains backend-focused; the AI Console UI was
  not redesigned.

## Validation summary

The Windows implementation gate completed 424 Python tests, the nine official
examples, all three probes, locked Rust formatting/Clippy/tests, the bounded
20-fixture differential corpus, the 10-fixture standard-library corpus, Native
standalone checks, extension compile/smoke tests, a zero-vulnerability
production npm audit, and VSIX content inspection. The Python suite's only
accepted warnings are the two Python 3.12 deprecations emitted by pinned
`lark-parser==0.12.0`.

This source work does not publish to PyPI or the VS Code Marketplace. Native
Core remains a preview, and Python remains the compatibility engine.
