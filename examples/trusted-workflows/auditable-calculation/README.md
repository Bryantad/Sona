# Auditable Calculation

This integer-cents invoice calculation is deterministic and needs only the
console capability. Proof Mode identifies the exact program bytes, output
bytes, Native Core engine, capability set, observed console effects, execution
result, and receipt integrity.

```powershell
New-Item -ItemType Directory -Force .sona\receipts | Out-Null
$receipt = ".sona\receipts\invoice-$([guid]::NewGuid()).json"
sona proof .\invoice.sona --receipt $receipt --engine native --summary
sona proof verify $receipt
sona proof inspect $receipt
```

The expected total is `12875` cents. This is an execution-evidence example,
not financial advice, an accounting control, or a regulatory certification.
