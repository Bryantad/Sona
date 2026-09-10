# Sona Package Manager Status and Roadmap

Sona `0.15.0` does not ship a public package registry, publishing service, or
Cargo-equivalent build manager.

## Current Foundation

- Sona `0.15.6` development hardens local-path package installation without
  introducing a registry.
- Schema-2 manifests and dependency locks are deterministic and atomically
  written.
- New locks identify `sha256-tree-v2` package content and retain read-only
  schema-1 verification compatibility.
- Package names and install destinations are project-contained; traversal,
  symlink sources, symlink trees, and overlapping targets are rejected.
- Installation uses resolve, validate, stage, verify, atomic commit, and
  rollback instead of mutating each live dependency in place.
- Local sibling file and directory dependencies remain supported.
- Standard-library module metadata is canonicalized through the manifest.
- Release hardening validates installed artifacts outside the repository.
- Hidden native modules are excluded from public discovery.

## Future Package Manager Goals

- Richer dependency version compatibility checks.
- Build provenance that can reference deterministic package identities without
  changing the frozen Proof Mode schema-1 receipt.
- Optional registry publishing.
- Trust policies connected to Guardian manifests.
- Clear separation between public modules and private runtime backends.

The immediate priority is reliable local packaging and metadata consistency.
Remote publishing and dependency resolution are future work.
