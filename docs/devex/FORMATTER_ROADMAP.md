# Formatter Roadmap

Sona `0.15.0` does not include a production formatter.

## Future Formatter Goals

- Stable formatting rules for `.sona` and `.smod`.
- Idempotent formatting.
- Clear diffs with minimal churn.
- Formatter tests tied to parser and diagnostics behavior.
- Editor integration after CLI behavior is reliable.

Formatter work should not change language semantics or hide parser errors.
