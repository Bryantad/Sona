# Receipt Redaction Spec 0.1 (Draft)

Status: Draft  
Target: `v0.11.0`

## Goals

- Deterministic, policy-driven receipt redaction.
- Stable canonical hashing after redaction.
- Compatibility with receipt signing and signature verification (sign redacted form).

## Profiles

- `dev`: redact `sensitive`, keep `internal`.
- `ci`: redact `sensitive`, keep `internal`.
- `prod`: redact `sensitive` and `internal`.

## Classification Tiers

- `public`: never redacted.
- `internal`: profile-dependent.
- `sensitive`: redacted by profile action rules.

Implemented default classification includes current receipt fields and future-facing event paths (tool/model/io payloads).

## Deterministic Transform

- Redaction token format:
  - `[REDACTED:sha256:<hash>]`
- Token hash seed:
  - canonical value
  - `receipt_id`
  - `policy_fingerprint` (receipt policy context)
- Arrays and objects preserve structure; scalar leaves are replaced deterministically.

## Hashing and Signing

- Canonical `receipt_hash` excludes signature envelope fields.
- Redaction removes signature envelope and recomputes `receipt_hash`.
- Signing is intended for redacted receipt artifacts:
  1. `sona receipt redact`
  2. `sona receipt sign`
  3. `sona receipt verify-signature`

## CLI

- `sona receipt redact <receipt.json> [--out ...] [--profile dev|ci|prod] [--policy ...] [--emit-manifest]`
- `sona receipt redact-dir <dir> [--out-dir ...] [--profile dev|ci|prod] [--policy ...] [--emit-manifest]`

## Manifest

Optional manifest output captures:

- input path/output path
- source receipt hash/redacted receipt hash
- redacted field/value counts
- policy fingerprint/profile

