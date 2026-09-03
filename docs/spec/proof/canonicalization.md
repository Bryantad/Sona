# Proof Canonicalization

Schema-1 canonical JSON is:

- UTF-8 encoded
- compact, with separators `,` and `:`
- lexicographically sorted object keys
- no trailing newline in the hash input

Stored receipt files may contain either the exact canonical JSON bytes or those
bytes followed by one LF byte. The optional LF is for terminal-friendly files
and is not part of `receipt_hash`.

Other JSON-equivalent storage is not canonical schema-1 storage. In particular,
key reordering, pretty printing, leading whitespace, trailing spaces, and more
than one trailing LF are rejected by verification.

`receipt_hash` is computed as:

1. Copy the receipt object.
2. Remove `receipt_hash`.
3. Encode the copy as schema-1 canonical JSON.
4. Compute SHA-256 over those bytes.
5. Store the lowercase label `sha256:<64 hex chars>`.

The cross-implementation vectors in
`tests/proof/vectors/schema1-vectors.json` record exact canonical payloads and
expected SHA-256 labels. Both the Rust producer tests and Python verifier tests
consume that same corpus. Changing a vector's established canonical bytes or
hash is a schema compatibility change, not an ordinary fixture update.
