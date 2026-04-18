# Guides

This directory contains practical guides for the current Sona runtime.

## Start Here

- [SONA_MEMORY_INTEGRATION.md](./SONA_MEMORY_INTEGRATION.md): external memory setup, demo flow, exact expected outputs, and failure-mode behavior.
- [COPILOT_PROMPT.md](./COPILOT_PROMPT.md): GitHub Copilot workflow guidance.
- [USE_ORIGINAL_WORKSPACE.md](./USE_ORIGINAL_WORKSPACE.md): workspace setup notes.

## Core Commands

Primary CLI command:

```powershell
sona run examples/hello_world.sona
```

Fallback if `sona` is not on `PATH`:

```powershell
python -m sona.cli run examples/hello_world.sona
```

## Related Docs

- `../troubleshooting/MEMORY_INTEGRATION.md`
- `../troubleshooting/README.md`
- `../../examples/README.md`
