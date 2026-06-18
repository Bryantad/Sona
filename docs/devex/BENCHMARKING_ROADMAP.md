# Benchmarking Roadmap

Sona `0.15.0` does not ship a full benchmark suite.

## Current Foundation

- Release gates validate correctness and packaging.
- Static probe performance is tracked for stdlib discovery.
- Examples are source-validated.

## Future Benchmark Goals

- CLI cold-start timing.
- Parser and interpreter microbenchmarks.
- Stdlib module import timing.
- Guardian snapshot and verify timing.
- Cross-platform baseline reporting.

Benchmarks should be reproducible and should not replace correctness tests.
