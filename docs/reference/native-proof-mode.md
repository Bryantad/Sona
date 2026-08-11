# Native Proof Mode

Native Proof Mode records bounded evidence for one Native Core execution. It
observes the existing native runtime; it does not select another engine, alter
program semantics, or provide a general security attestation.

```text
sona proof app.sona --receipt proof.json --engine native
sona proof app.sbc --receipt proof.json --allow-fs-read
sona proof app.sona --receipt proof.json --summary
```

The receipt destination is required, its parent directory must already exist,
and the destination must be new. Proof Mode never overwrites, truncates, or
merges an existing receipt. Writing the requested receipt is runner-owned and
does not grant a program filesystem-write access.

## Evidence contract

Proof Mode accepts `.sona` source and version-1 source-backed `.sbc`
containers. A container must first pass the normal Native Core container
validation, including its exact UTF-8 source payload. Invalid containers keep
their existing `SONA-NATIVE-BYTECODE-*` diagnostic and do not produce a Proof
receipt.

Receipts use `sona.native-proof.schema-1`. They record only:

- exact-source and container SHA-256 identities and byte counts;
- Native Core and no-Python/fallback flags;
- explicitly granted capabilities;
- execution status, duration, exit status, and stable diagnostic coordinates;
- SHA-256/byte-count summaries of stdout and stderr; and
- redacted filesystem, console, stdin, and unavailable-network effects.

No receipt stores source text, raw paths, stdout/stderr bodies, stdin values,
environment values, credentials, request bodies, temporary paths, or operating
system error text. Filesystem targets use a new execution-local
`hmac-sha256:` fingerprint. The key is never stored, so receipts cannot usefully
correlate the same path across executions. Stdin effects never include a target
or value fingerprint.

`receipt_hash` is SHA-256 over the compact canonical UTF-8 JSON receipt with
the `receipt_hash` member omitted. Object keys are lexicographically sorted,
arrays retain execution order, and the newline written to the JSON file is not
included in the digest. Hashes use lowercase `sha256:<hex>` notation.

## Diagnostics and compatibility

`PROOF-001` through `PROOF-007` belong exclusively to Proof Mode invocation,
input, receipt destination, creation, serialization, and finalization
failures. Diagnostics produced by the program retain their existing Sona
identifiers: Proof Mode does not reclassify parser, container, VM, runtime,
engine, capability, Guardian, or host failures.

When a program fails and the receipt persists, Sona prints the original program
diagnostic and stores its identifier in the receipt. When persistence itself
fails, Sona prints the relevant `PROOF-*` diagnostic and makes no proof-success
claim. A final path may remain after a post-publication durability failure; it
must not be treated as publication-certified.

Without `--summary`, a successfully persisted `sona proof` has the same
program-visible stdout, stderr, exit result, VM semantics, and runtime
diagnostics as an equivalent native `sona run`. Only the explicitly requested
evidence side effect differs.

## Interactive summary

Pass `--summary` when a person is watching the terminal and needs a concise
confirmation that the receipt was saved. After a successful execution and
receipt publication, Sona writes a labeled summary to stderr with the receipt
path, Native Core engine, observed-effect count, output byte counts, duration,
and receipt hash.

The summary is presentation-only: it is not emitted for program or receipt
failures, is not included in the receipt's output hashes, and does not change
the receipt contents, receipt hash, program stdout, or exit result. Leave the
flag off for the exact `sona run`-compatible stdout/stderr contract used by
scripts and automated tests.

## Limits of the claim

Proof Mode creates redacted, self-hashed, tamper-evident-after-creation Native
Core execution evidence. It does not provide cryptographic signer identity,
machine or remote attestation, trusted-hardware proof, operating-system
integrity proof, Guardian linkage, receipt verification, or full Python/native
semantic parity. Those remain post-0.15.4 work.
