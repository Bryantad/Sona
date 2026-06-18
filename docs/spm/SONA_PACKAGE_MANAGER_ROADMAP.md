# Sona Package Manager Roadmap

Sona `0.15.0` does not ship a public package registry, publishing service, or
Cargo-equivalent build manager.

## Current Foundation

- Package metadata is documented.
- Standard-library module metadata is canonicalized through the manifest.
- Release hardening validates installed artifacts outside the repository.
- Hidden native modules are excluded from public discovery.

## Future Package Manager Goals

- Local package validation.
- Dependency metadata and compatibility checks.
- Lockfile semantics.
- Optional registry publishing.
- Trust policies connected to Guardian manifests.
- Clear separation between public modules and private runtime backends.

The immediate priority is reliable local packaging and metadata consistency.
Remote publishing and dependency resolution are future work.
