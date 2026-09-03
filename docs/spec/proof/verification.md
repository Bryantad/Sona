# Proof Verification

`sona proof verify <receipt>` performs local structural and integrity
verification of a Proof Mode schema-1 receipt.

Verification validates:

- receipt file is a regular UTF-8 JSON file
- receipt root is a JSON object
- stored JSON is canonical, with an optional trailing LF
- `receipt_hash` matches canonical content with `receipt_hash` omitted
- schema fields identify Proof Mode schema-1
- runtime identity fields are present
- engine identity is Native Core
- Python requirement, Python embedding, and fallback are all false
- optional Native runtime identity contains a valid executable SHA-256/byte
  count and optional full lowercase Git revision
- capability records contain explicit booleans
- execution records are internally consistent
- effect records are contiguous, redacted, and use known outcomes
- optional normalized effect fields are paired, syntactically valid, and match
  the registered low-level operation mapping

For a recognized legacy `scope` and `operation` pair, the verifier adds the
corresponding normalized `effect` and `support` to its result for display and
automation. It does not rewrite the receipt or its hash input. An unknown
legacy operation remains structurally valid and unclassified. An unknown
operation cannot claim a registered normalized effect.

Verification fails closed with `PROOF-VERIFY-*` diagnostics. Diagnostics avoid
source text, raw output bodies, stdin values, credentials, environment values,
and raw operating-system error text.

## Integrity boundary

Verification establishes that the stored canonical receipt matches its
`receipt_hash` and satisfies the schema-1 structure. Altering a hashed field
without re-sealing the receipt fails integrity verification.

Because schema-1 is self-hashed rather than signed, a party able to replace the
receipt can also compute a new self-hash. Verification does not independently
replay the program or prove that a re-sealed source, output, or capability hash
describes reality. See `threat-model.md` for the trust boundary.

General verification reports whether a Guardian object is present but does not
need local Guardian state. `sona guardian proof verify` first reuses this exact
verifier, then checks baseline and optional policy binding fields against the
explicit project root.

## Human output contract

`sona proof verify <receipt>` and `sona proof inspect <receipt>` use the same
verified result. Their human views state plain-language facts before technical
identities:

1. receipt and self-hash integrity validity;
2. execution success or failure and recorded exit code;
3. source or source-backed bytecode kind;
4. Sona runtime version and Native Core identity;
5. whether Python was required or embedded and whether fallback was used;
6. Guardian binding presence;
7. granted and denied capabilities;
8. ordered normalized effects, outcomes, and support statuses; and
9. program, stdout, stderr, and receipt byte-count/SHA-256 identities.

These views do not add claims beyond the verified receipt. `--json` preserves
the machine-readable verifier-result shape.

## Generation coordinator

The Python-installed command recognizes
`sona proof <program> --receipt <new-receipt>` as a generation request and
forwards the Native Proof arguments unchanged to the standalone Rust producer.
It resolves an explicit `SONA_NATIVE_BINARY` first and otherwise only
`sona-native` from `PATH`. It never resolves a generic `sona`, invokes a shell,
or falls back to Python execution. Native process streams and exit status are
preserved.

`verify`, `inspect`, and help remain Python-owned actions. A coordinator launch
failure is not a schema verification result because no producer ran and no
receipt exists.
