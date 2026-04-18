# Runtime Layers

Sona is a programming language first.

The interpreter and grammar remain the primary public surface. Runtime memory, checkpoints, continuation, and goal inference exist to support execution, inspection, and recovery of Sona programs. They do not define the language or replace the interpreter as the product boundary.

Current layer model:

1. Language layer: grammar, AST, interpreter semantics, standard library contracts.
2. Stable runtime data layer: public memory models, enums, payload normalization, and schema versioning exposed from `sona.runtime.memory`.
3. Advanced host/runtime layer: storage, promotion, retrieval, inspection, consolidation, and execution-intake helpers exposed from `sona.runtime.memory.advanced`.
4. Internal orchestration layer: checkpoint restoration, goal continuation, inference, and transition orchestration exposed from `sona.runtime.memory.internal`.

Boundary rule:

- Default imports should favor language-facing and stable data-model APIs.
- Host integrations may opt into `advanced` explicitly.
- Goal/checkpoint orchestration stays internal or experimental unless a stable host contract is intentionally promoted.

This keeps Sona's public identity centered on the language while still allowing the runtime to evolve behind explicit import boundaries.