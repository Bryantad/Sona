# Deployment Evidence Reference

This is a bounded local staging workflow, not a cloud deployment platform. It
copies the committed example artifact into `.sona/deployments/staging` through
Native Core and records the filesystem read/write boundaries in Proof Mode.

```powershell
New-Item -ItemType Directory -Force .sona\receipts | Out-Null
sona guardian init --project-root .
sona guardian check --project-root .
$receipt = ".sona\receipts\deploy-$([guid]::NewGuid()).json"
sona proof .\deploy.sona --receipt $receipt --engine native `
  --allow-fs-read --allow-fs-write --guardian-root . --summary
sona proof verify $receipt
sona guardian proof verify --project-root . --receipt $receipt
```

Evidence and metadata must be distinguished:

| Value | Current status |
| --- | --- |
| Exact `deploy.sona` bytes | Identified by the receipt's program SHA-256 |
| Native engine, capability grants, filesystem boundaries, result, and output | Proof Mode evidence within schema-1 limits |
| Application version `1.0.0` | Declared metadata embedded in preserved source |
| Source revision `example-fixture-r1` | Declared example metadata, not a Git-provider assertion |
| Artifact SHA-256 | Declared metadata; independently check the artifact before use |
| Environment label `local-staging` | Declared metadata, not authenticated host identity |

Verify the committed artifact independently:

```powershell
(Get-FileHash .\artifact\app.txt -Algorithm SHA256).Hash.ToLowerInvariant()
```

The expected digest is
`9d9d72726b51c85cb293b2383e180f4f39c12dbbe66d41acab811d5a45687de8`.
The receipt's source hash binds the declarations inside `deploy.sona`; it does
not prove those declarations are true, authenticate the machine, prove a
remote environment, or provide rollback.

