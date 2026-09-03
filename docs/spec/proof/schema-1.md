# Proof Mode Schema 1

Schema identifier: `sona.native-proof.schema-1`

Schema-1 receipts are JSON objects with these required fields:

- `schema_id`: must be `sona.native-proof.schema-1`
- `schema`: must be `1`
- `receipt_type`: must be `native_execution_proof`
- `generated_at_utc`: ISO UTC timestamp in `YYYY-MM-DDTHH:MM:SSZ` form
- `sona_version`: non-empty Sona runtime version string
- `engine`: Native Core identity record
- `program`: source or source-backed bytecode identity
- `capabilities`: explicit runtime capability booleans
- `execution`: execution status, output digests, and output byte counts
- `effects`: ordered observed effect records
- `receipt_hash`: self-hash over canonical receipt content without this field

The verifier accepts existing 0.15.4 schema-1 receipts and does not require a
Guardian binding unless the caller uses Guardian-specific verification.

## Effect extension

Every effect retains the schema-1 low-level evidence fields `sequence`,
`scope`, `operation`, `outcome`, and optional redacted `target`.

Recognized operations emitted by current Native Core also contain both of
these optional schema-1 extension fields:

- `effect`: registered uppercase normalized identifier such as `FS.READ`
- `support`: one of `SUPPORTED`, `PARTIAL`, `UNOBSERVED`, or `UNAVAILABLE`

The fields form a pair: a receipt cannot contain only one. If present, the
pair must exactly match the registered mapping for `scope` and `operation`.
They add a stable display and automation vocabulary without replacing the
low-level observation. Existing receipts that omit both fields retain their
original meaning and self-hash.

## Optional Guardian binding

The optional `guardian` object uses
`sona.guardian-proof-binding.schema-1`. Its required baseline-only fields are:

- `schema_id`
- `baseline_snapshot_id`
- `baseline_sha256`
- `trusted_config_sha256`
- `program_baseline`, with value `tracked`

Policy-aware Guardian state adds `policy_sha256` and
`policy_enforced: true` inside this nested object. These are optional schema-1
extensions, not new core receipt fields. General Proof Mode verification
accepts both forms. Guardian-specific verification always validates the
baseline fields and validates policy identity when the extension is present.

## Optional Native runtime identity

New 0.15.5 Native producers add `engine.runtime_identity` without changing the
required schema-1 engine fields. The object contains:

- `native_binary.sha256`: SHA-256 of the running Native CLI executable;
- `native_binary.bytes`: that executable's byte count; and
- optional `source_revision`: `git:` followed by a full 40-character lowercase
  hexadecimal revision supplied by the build environment.

If `runtime_identity` is present, `native_binary` is required and every field
is validated. Legacy schema-1 receipts without this extension remain valid.
These self-declared, self-hashed fields support comparison with separate
release records; they do not authenticate the binary, revision, build system,
host, or operator.
