# Proof Mode Assurance Levels

Proof Mode schema-1 provides deterministic receipt integrity and structured
local execution evidence. Its assurance boundary is intentionally narrower
than authenticated provenance or attestation.

| Assurance property | Schema-1 status | Meaning |
| --- | --- | --- |
| Integrity | Available | Canonical bytes, required structure, and the stored self-hash agree |
| Authentication | Not provided | No signer or producer identity is authenticated |
| Attestation | Not provided | No remote, hardware, operating-system, or trusted-runtime attester vouches for the execution |
| Trusted anchor | Not provided | No protected key, transparency service, trusted timestamp, or hardware root anchors the claim |

An actor who can replace a receipt can recompute its self-hash. Therefore
schema-1 detects accidental corruption and unsealed edits to the stored
receipt, but it is not tamper-proof and must not be marketed as authenticated
or independently tamper-evident evidence.

Guardian can bind a receipt to project-local policy and baseline hashes. Those
files express what the local operator selected as trusted state; they are not a
protected trust anchor. The compatibility command `sona guardian proof attest`
records a successful local audit check. Its `attested` status is not
cryptographic or remote attestation and adds no authentication.

Published package checksums, operating-system code signing, and third-party CI
records may be useful distribution controls, but they are separate from the
schema-1 receipt assurance claim unless a future reviewed trust layer binds
them explicitly.

