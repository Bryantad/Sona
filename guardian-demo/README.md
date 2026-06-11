# Guardian Recovery Demo

This fixture demonstrates one narrow Guardian recovery flow:

1. Initialize Guardian for a small project.
2. Capture a known-good snapshot.
3. Modify a watched `.sona` file.
4. Detect drift and show the changed file.
5. Apply healing, which quarantines the suspect version and restores the
   trusted snapshot.
6. Verify the restored project.

Run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File guardian-demo\run_demo.ps1
```

The script writes JSON command output under `guardian-demo/output/`. Guardian
state lives under `guardian-demo/.sona/guardian/`, which is local generated
state and is ignored by Git.

