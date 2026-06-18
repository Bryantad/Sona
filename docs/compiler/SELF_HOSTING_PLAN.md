# Self-Hosting Plan

Sona `0.15.0` is not self-hosting. The compiler, runtime, and packaging flow
still depend on Python.

## Proposed Stages

1. Keep the Python implementation as the reference behavior.
2. Move more standard-library behavior into Sona-authored modules where safe.
3. Define compiler data structures that can be represented in Sona code.
4. Port isolated compiler utilities only after test coverage is strong.
5. Build a partial compiler in Sona for validation, not replacement.
6. Attempt full self-hosting only after native backend parity is proven.

Self-hosting is a long-term independence milestone. It is not a 0.15.0 release
claim.
