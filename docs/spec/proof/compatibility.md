# Proof Compatibility

Sona 0.15.5 preserves schema-1 compatibility with Sona 0.15.4 Proof Mode
receipts.

Compatibility rules:

- Existing canonical schema-1 receipts remain verifiable.
- Existing effect records without normalized fields remain verifiable. For
  recognized low-level operations, the verifier may infer normalized fields in
  its returned view without changing receipt bytes or receipt identity.
- New producers may add paired `effect` and `support` fields. Verifiers reject
  incomplete, invalid, or false mappings and preserve unknown legacy
  operations without inventing a classification.
- A single trailing LF after canonical JSON remains acceptable.
- Guardian-bound receipts remain valid general Proof receipts.
- Legacy Guardian bindings without policy fields remain valid.
- Policy-aware Guardian bindings add fields only inside the existing optional
  `guardian` object and do not change schema-1 core fields or canonicalization.
- New Native producers may add a validated `engine.runtime_identity` extension
  with exact executable identity and an optional full source revision. Legacy
  receipts without it retain their original normalized engine view.
- General Proof verification does not require Guardian state.
- Guardian-specific verification may add baseline and binding checks after the
  general Proof verifier succeeds.

The compatibility gate includes a receipt emitted by an actual Sona Native
0.15.4 binary. Later schema-1 verifiers must continue accepting that fixture.
The shared interoperability vectors in
`tests/proof/vectors/schema1-vectors.json` freeze canonical payload bytes and
their expected receipt hashes for both Rust and Python tests.
Those vectors and the frozen 0.15.4 fixture are unchanged by the normalized
effect extension. The separate
`tests/proof/vectors/effect-vocabulary.json` corpus locks producer/verifier
classification agreement without rewriting historical evidence.

Schema-1 field meanings and canonicalization cannot change incompatibly in a
later verifier release. A change that breaks those semantics requires a new
schema identifier; it must not silently reinterpret an existing schema-1
receipt.

Schema-1 verification rejects fallback receipts, Python-required receipts,
Python-embedded receipts, unsupported schema identifiers, and receipts whose
self-hash no longer matches their canonical contents.
