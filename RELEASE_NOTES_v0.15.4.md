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

## Native Proof Mode

- `sona proof <program.sona|program.sbc> --receipt <path>` records redacted,
  self-hashed Native Core execution evidence without changing the program's
  native runtime behavior.
- Receipts identify exact source/container bytes, granted capabilities,
  sanitized effects, outcome, diagnostics, and output hashes. They never store
  source, paths, output bodies, stdin values, credentials, or environment data.
- `PROOF-001..008` are reserved for Proof Mode infrastructure. Program parser,
  container, VM, runtime, engine, and capability diagnostics retain their
  established identifiers.
- `--summary` adds a concise terminal confirmation after a successful receipt
  is saved, without changing the receipt or the default scripted output.
- `--guardian-root <project>` opt-in binds a proof to an initialized,
  baseline-tracked Guardian project without importing Python, executing
  Guardian, or recording the project path in the receipt. Binding failures are
  `PROOF-008` and occur before execution.
- `sona guardian proof verify|attest|history` provides read-only receipt
  verification, clean-project local attestation, and redacted audit history.
  Attestation records the receipt hash and Guardian anchor only; it does not
  copy program paths, source, output, or the receipt itself.
- This is tamper-evident-after-creation evidence, not signer identity, machine
  or remote attestation, trusted-hardware proof, operating-system integrity
  proof, or a claim of Python/Native parity. The Guardian chain is local and
  does not protect against a party able to alter both local Guardian state and
  the receipt.

## Compatibility

- Valid 0.15.3 Python-compatible programs, implicit final-statement function
  values, cognitive runtime behavior, existing Guardian interfaces, and
  workspace module precedence are preserved. Guardian's new Proof helpers are
  additive.
- Existing public modules remain importable. Canonical aliases are quiet for
  the rest of the 0.15.x line.
- The tracked VS Code extension remains backend-focused; the AI Console UI was
  not redesigned.

## Validation summary

The release validation surface covers the Python suite, official examples,
static probes, locked Rust formatting/Clippy/tests, bounded differential and
standard-library corpora, Native standalone checks, extension compile/smoke
tests, production dependency audit, VSIX inspection, and the Guardian-bound
Proof verification/attestation chain. The Python suite's only accepted
warnings are the two Python 3.12 deprecations emitted by pinned
`lark-parser==0.12.0`.

Final publication certification must rebuild the artifacts from the final
commit in a clean Windows release environment, including its process-isolation
gate and the required cross-platform Python and Native checks.

This source work does not publish to PyPI or the VS Code Marketplace. Native
Core remains a preview, and Python remains the compatibility engine.
