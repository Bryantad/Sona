# Receipt Bundle Specification v0.2

**Status:** Implemented  
**Since:** Sona 0.11.0

## Overview

A receipt bundle is a portable, self-verifiable JSON artifact containing:

- All receipts from a directory
- A manifest with per-receipt integrity hashes
- A chain directory for O(1) receipt lookup by hash or ID
- Chain verification certificate
- Optional policy snapshot
- Optional workspace lockfile

## Bundle Structure

```json
{
  "bundle_version": "0.2",
  "bundle_kind": "receipt_export",
  "created_at_utc": "<ISO 8601 timestamp>",
  "source_dir": "<absolute POSIX path>",
  "manifest": {
    "entries": [
      {"path": "000.receipt.json", "sha256": "<hex>", "size": <int>}
    ],
    "manifest_hash": "<hex>"
  },
  "chain_directory": {
    "by_hash": {"<receipt_sha256>": "<filename>"},
    "by_id": {"<receipt_id>": "<filename>"}
  },
  "chain_verification": { "...": "enriched chain certificate" },
  "receipts": [
    {"path": "000.receipt.json", "receipt": { "...": "full receipt" }}
  ],
  "receipt_count": <int>,
  "policy_snapshot": { "...": "optional" },
  "lockfile": { "...": "optional, no timestamp" },
  "bundle_hash": "<hex>"
}
```

## Canonicalization

**Single canonical JSON rule set** used for all governance hashing in the bundle surface:

- `sort_keys=True`
- `separators=(",", ":")`
- `ensure_ascii=False`
- UTF-8 encoding

This matches the canonicalization used by receipt signing (`canonical_receipt_signing_payload`).

No secondary canonicalizer with `ensure_ascii=True` is used.

## Hashing Rules

### Manifest Entry Hash

```
manifest.entries[].sha256 = sha256(canonical_receipt_payload(receipt).encode("utf-8"))
```

This equals `receipt_sha256(receipt)` — the receipt's own hash contract. The bundle is a **receipt artifact integrity** container.

### Manifest Hash

```
manifest.manifest_hash = sha256(_canonical_json_bytes({"entries": manifest.entries}))
```

Computed over the entries array only, excluding `manifest_hash` itself.

### Bundle Hash

```
bundle.bundle_hash = sha256(_canonical_json_bytes(bundle_without_bundle_hash))
```

Computed over the entire bundle object excluding the `bundle_hash` field.

## Verification

`verify_receipt_bundle(bundle)` checks:

1. **Bundle hash**: recomputes hash over bundle minus `bundle_hash`, compares
2. **Manifest hash**: recomputes hash over entries, compares
3. **Entry hashes**: for each receipt, verifies `receipt_sha256(receipt) == manifest_entry.sha256`

Returns:

```json
{
  "ok": true,
  "reason": "ok",
  "bundle_hash_ok": true,
  "manifest_ok": true,
  "manifest_hash_ok": true,
  "receipt_count": 3,
  "entry_mismatches": []
}
```

## Chain Directory

- `by_hash`: maps `receipt_sha256(receipt)` → filename
- `by_id`: maps `receipt_id` → filename
- **Raises `ValueError` on collisions** (governance invariant)

## Optional Lockfile

When `include_lockfile=True` and `workspace_dir` is provided, the bundle embeds a deterministic lockfile payload (no timestamp) via `lockfile_payload()`.

## CLI

```
sona receipt export --dir .sona/receipts --output bundle.json --include-lock --workspace .
```

## Changes from v0.1

- Added `manifest` with per-receipt integrity hashes
- Added `chain_directory` for O(1) lookup
- Added optional `lockfile` embedding
- Bundle hash now uses `ensure_ascii=False` (consistent with signing canonicalization)
- `verify_receipt_bundle()` function added
- CLI: `--include-lock` and `--workspace` flags
