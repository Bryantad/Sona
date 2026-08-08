# Runtime capabilities

Python-compatible runs retain the 0.15.3 process-access behavior. With
`sona run --safe`, reads are confined to the project root and secret reads,
writes, and network access are denied.

Native Core defaults to console access only. Grant effects separately:

```text
sona run app.sona --engine native --allow-fs-read
sona run app.sona --engine native --allow-fs-write
sona run app.sona --engine native --allow-fs-read --allow-fs-write
```

`--allow-network` grants the network policy bit, but native HTTP remains
unavailable in 0.15.4. Process execution and environment access cannot be
granted through these flags.

Workspace `.smod` modules retain precedence over built-in Native Core host
modules. The host registry is a fallback, not an override.

Native Proof Mode uses the same Native Core grants while writing an explicit
runner-owned evidence receipt:

```text
sona proof app.sona --receipt proof.json --engine native --allow-fs-read
```

It does not grant any capability beyond the listed flags. See [Native Proof
Mode](../native-proof-mode.md) for receipt redaction and diagnostic ownership.
