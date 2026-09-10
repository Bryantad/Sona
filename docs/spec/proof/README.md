# Proof Mode Specification

This directory defines the Proof Mode schema and verification contracts
used by Sona 0.15.6 foundation work.

Proof Mode receipts are local execution evidence. They are not signatures,
identity assertions, trusted timestamps, operating-system integrity claims,
remote attestations, or trusted-hardware proofs.

See [Assurance levels](assurance.md) for the explicit integrity,
authentication, attestation, and trusted-anchor distinction.

Start here:

- `schema-1.md` defines the receipt fields.
- `canonicalization.md` defines canonical JSON and receipt hashing.
- `verification.md` defines `sona proof verify <receipt>`.
- `effects.md` defines capability and effect records.
- `automation.md` defines the boundary between AI metadata, runtime evidence,
  and advisory review.
- `compatibility.md` defines schema-1 compatibility.
- `threat-model.md` defines claims and non-claims.

## Interoperability certification

The schema-1 contract is exercised across independent implementations:

```text
Rust Proof Mode producer
        -> canonical schema-1 receipt
        -> Python sona.proof verifier
```

The installed workflow is coordinated as:

```text
sona proof <program> --receipt <receipt>  -> standalone Rust producer
sona proof verify <receipt>               -> Python verifier
sona proof inspect <receipt>              -> Python verified view
```

The test contract covers real `.sona` and source-backed `.sbc` receipts,
Native `run`/`proof` behavior parity, corruption rejection, strict canonical
storage, shared Rust/Python golden vectors, a shared normalized-effect
vocabulary, and a frozen Native 0.15.4 receipt.
