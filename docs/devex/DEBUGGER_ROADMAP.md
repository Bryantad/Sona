# Debugger Roadmap

Sona `0.15.0` does not include production debugger support.

## Future Debugger Goals

- Source-level breakpoints.
- Step in, step over, and step out.
- Local variable inspection.
- Stack traces aligned with user-facing diagnostics.
- Guardian-aware recovery reports for failed debugging sessions.

Debugger support should be built after runtime execution and source mapping are
stable enough to avoid misleading developers.
