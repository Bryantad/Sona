# Sona Compiler Architecture Roadmap

Sona `0.15.0` is not a native compiler release. It keeps the current
Python-backed parser, interpreter, runtime, and standard-library loading path.

## Current Architecture

- Source files are parsed and executed by the packaged Python runtime.
- Public standard-library modules are discovered through the canonical manifest.
- Native Python modules remain internal runtime backends or compatibility
  layers.
- Guardian and accessibility modules are runtime-backed features, not compiler
  passes.

## Future Architecture Targets

- A stable language-semantics layer independent from Python implementation
  details.
- A typed or structured intermediate representation.
- Backend interfaces that can target interpreter execution first and native
  compilation later.
- Compatibility tests shared across interpreter and future compiler backends.

No 0.15.0 documentation or release material should imply that this future
architecture is already complete.
