# Trusted Workflow Examples

These examples show the practical 0.15.6 workflow: select a small program,
grant only the capabilities it needs, run it through Proof Mode, and verify the
receipt. They use real Sona operations and state their evidence limits.

| Example | Runtime | What it demonstrates |
| --- | --- | --- |
| [AI action receipt](ai-action-receipt/README.md) | Native Core + Proof Mode + Guardian | A controlled file action over externally supplied proposal text |
| [Auditable calculation](auditable-calculation/README.md) | Native Core + Proof Mode | Deterministic invoice arithmetic and output identity |
| [Service/API workflow](service-api/README.md) | Python compatibility | A real loopback HTTP request, explicitly without Native Proof evidence |
| [Deployment evidence](deployment-evidence/README.md) | Native Core + Proof Mode + Guardian | A bounded local staging copy with declared deployment metadata |

Proof Mode receipts are self-consistent local evidence. They are not signed,
authenticated, remotely attested, or proof of who initiated an action.

