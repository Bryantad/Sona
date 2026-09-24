# Example B — Durable pipeline with explicit recovery

The three-step `build → test → package` pipeline writes its lifecycle to the
local hash-chained workflow journal. It is an API example: operations are
registered in this script and do not execute arbitrary persisted commands.

```powershell
python examples/durable-workflow/run_pipeline.py --interrupt
python examples/durable-workflow/run_pipeline.py
python examples/durable-workflow/run_pipeline.py --resume-interrupted
```

The first command leaves one step durably marked as running and exits. The
second opens the journal inertly and reports that recovery needs a decision.
Only the third explicitly retries that step from the beginning. Use a fresh
working directory for another complete demonstration, or pass a different
`--root`. Persisted operation names do not automatically execute on open.
