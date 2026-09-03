# AI Action Receipt

This example places an externally supplied proposal behind a fixed Sona tool
boundary. The included `proposal.txt` stands in for text that an AI system may
have produced; this example does **not** invoke a model or claim that Proof Mode
establishes AI identity, authorship, or request-to-action causality.

The real evidence chain is:

```text
external proposal
  -> Guardian capability decision
  -> Native file read and write
  -> observed FS.READ, FS.WRITE, and STDOUT.WRITE effects
  -> Proof Mode receipt
  -> shared receipt and Guardian verification
```

From this directory in PowerShell:

```powershell
New-Item -ItemType Directory -Force .sona\receipts | Out-Null
sona guardian init --project-root .
sona guardian check --project-root .
$receipt = ".sona\receipts\ai-action-$([guid]::NewGuid()).json"
sona proof .\workflow.sona --receipt $receipt --engine native `
  --allow-fs-read --allow-fs-write --guardian-root . --summary
sona proof verify $receipt
sona proof inspect $receipt
sona guardian proof verify --project-root . --receipt $receipt
```

The result is written below `.sona/workflow`, which Guardian excludes from the
tracked source baseline. Preserve the exact source and receipt together when
reviewing the evidence.

