# Sona Native Independence Roadmap

Sona `0.15.0` still uses the Python-backed runtime. The release establishes
runtime metadata, cognitive-accessibility support, Guardian local resilience,
and release hardening, but it does not complete native compiler independence.

## Current 0.15.0 Status

- Python remains the host runtime.
- `.sona` and `.smod` execution still flows through the packaged interpreter.
- Standard-library discovery is manifest-backed and static where possible.
- Guardian provides local project recovery, not a native runtime sandbox.

## Not Complete In 0.15.0

- Self-hosting compiler.
- LLVM code generation.
- Standalone `.exe` or `.app` generation.
- Custom native runtime engine.
- Native garbage collector.
- Ownership model.
- Native memory management.

## Staged Direction

1. Keep the Python-backed runtime stable and well tested.
2. Separate language semantics from host-runtime implementation details.
3. Define a compiler intermediate representation.
4. Prototype an LLVM backend behind explicit experimental gates.
5. Validate native execution against the Python-backed runtime suite.
6. Treat self-hosting as a long-term milestone after native execution is
   reliable.

The near-term goal is runtime correctness and developer trust, not premature
claims of Python independence.
