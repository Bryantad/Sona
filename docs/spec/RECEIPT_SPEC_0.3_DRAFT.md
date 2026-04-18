# Sona Receipt Spec 0.3 (Draft)

## Date
- February 24, 2026

## Status
- Draft
- Target freeze: v0.10.4-v0.10.5

## Scope
- Directory integrity receipts (`sona receipt scan|build`) and baseline execution receipts.

## Required Fields (Directory Integrity)
- `receipt_kind`
- `receipt_version`
- `mode`
- `receipt_id`
- `root_path`
- `header`
- `policy`
- `files`
- `summary`
- `receipt_hash`

## Header Fields
- `policy_fingerprint`:
  - hash of effective receipt policy (include/exclude/follow_symlinks).
- `engine_policy_fingerprint`:
  - hash of active policy engine rule set.
- `prev_receipt_hash`:
  - optional hash-chain pointer to prior receipt.
- `receipt_hash`:
  - canonical SHA-256 hash of current receipt payload.

## Canonical Hashing
- Canonical payload generation:
  - JSON object sorted keys
  - compact separators `,` and `:`
  - `receipt_hash` fields removed before hashing
- Hash algorithm:
  - SHA-256 (lowercase hex)

## Tree Hash
- `summary.tree_sha256` computed from sorted file entries using:
  - `path + "\n" + sha256 + "\n" + size + "\n"`

## Verification Behavior
- Verify compares:
  - tree hash match
  - structural diff (`added/removed/changed`)
  - policy fingerprint match (if expected is present)
  - engine policy fingerprint match (if expected is present)

## Chain Semantics (Draft)
- `prev_receipt_hash` links receipts into a linear chain.
- Chain validation is local to current project context.
- Chain write policy:
  - explicit (`--prev-receipt` or `--prev-hash`) in v0.10.4.
  - automated chain management is deferred.

## Redaction and Signature (Planned)
- Redaction markers and signature blocks are planned for next draft.
- Not part of required v0.3 fields yet.
