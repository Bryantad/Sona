# Runtime CLI and VS Code Status Surface (0.16.0 Phase 15)

## CLI commands

`sona workflow list` and `sona workflow inspect <workflow-id>` read validated
snapshots from `.sona/workflows` (or an explicitly supplied `--root`). Opening
the journal may repair a derived snapshot from its authoritative hash-chained
events. The commands never resume, schedule, or execute workflow steps. JSON
output uses schema version 1; human-readable output is available with
`--format text`.

`sona runtime status` returns a read-only schema-1 summary of registered model
descriptors, persisted workflows, Guardian's project-local scope, Proof's
per-execution receipt model, and resource-reporting classifications. It does
not load a model or probe external providers. Model registration is not model
readiness.

`sona service status` is intentionally honest: `ServiceSupervisor` state is
owned by an application process. A standalone CLI process cannot discover
services owned by another process, and no daemon or cross-process registry is
implemented in this phase. The command reports `process_local`, not “zero
services are running.”

`sona doctor --format json` includes the runtime status object under `runtime`
while preserving the existing text-oriented default. This path does not
invent runtime state if the workflow journal is invalid; it reports the
stable `SONA-RUNTIME-STATUS-UNAVAILABLE` code.

## VS Code Runtime view

The **Sona Runtime** view refreshes from `sona runtime status --format json`.
It renders actual registered descriptor IDs, persisted workflow IDs/states,
and the returned service, Guardian, Proof, and resource-scope descriptions.
It labels model load readiness as “not probed,” does not imply services are
globally observable, and shows an unavailable state when the CLI output fails
schema validation. Refresh is the only action; the view does not start,
cancel, approve, resume, or modify work.

The view is informational. Proof receipt verification remains in the separate
Proof Mode Explorer, Guardian checks remain project-scoped CLI operations, and
service commands do not control another process.
