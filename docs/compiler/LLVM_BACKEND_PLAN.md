# LLVM Backend Plan

Sona `0.15.0` does not include LLVM code generation. LLVM support is a future
compiler-backend roadmap item.

## Readiness Requirements

- Stable language semantics documented independently from Python internals.
- A compiler IR with deterministic lowering rules.
- Runtime ABI boundaries for strings, lists, maps, errors, and modules.
- A test suite that compares interpreter results with generated-code results.
- Clear unsafe-feature boundaries for native memory and host calls.

## Non-Goals For 0.15.0

- Emitting LLVM IR.
- Producing native object files.
- Producing standalone binaries.
- Replacing the Python-backed runtime.

LLVM work should begin as an experimental backend only after the interpreter
surface is stable enough to serve as the correctness oracle.
