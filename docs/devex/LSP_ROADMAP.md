# LSP Roadmap

Sona `0.15.0` does not ship production-ready LSP completion. Current developer
experience work focuses on static discovery, CLI probes, examples, diagnostics,
and release hardening.

## Current Foundation

- Static stdlib discovery through manifest metadata.
- Hidden-module filtering for user-facing catalogs.
- `.sona` and `.smod` editor support through the extension track where present.

## Future LSP Goals

- Completion from the canonical manifest.
- Hover documentation from stdlib docs.
- Diagnostics aligned with CLI errors.
- Go-to-definition for local modules.
- Import validation without eager runtime execution.

LSP work should remain metadata-driven and should not require importing every
runtime module.
