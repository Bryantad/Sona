# Packages in Sona v0.15.5 (local only)

Sona `0.15.5` does not ship a public package registry. This release hardens
the existing local-path Sona Package Manager (SPM)
without adding downloads, publishing, or package signing.

SPM is also available as a standalone tool repository:
<https://github.com/Bryantad/Spm>.

## Commands

```bash
sona pkg init
sona pkg add local_name ../local-package
sona pkg install
sona pkg lock
sona pkg verify
sona pkg list
```

Use `sona pkg install --dev` to include development dependencies. The shorter
`spm` console command exposes the same parser and transaction engine for
compatibility; neither command accesses a package registry in 0.15.x.

## Project manifest: `sona.json`

`spm init` creates deterministic, sorted schema-2 JSON and never replaces an
existing manifest.

```json
{
  "dependencies": {
    "my_pkg": {
      "path": "../my_pkg",
      "version": "*"
    }
  },
  "devDependencies": {},
  "name": "my-project",
  "sona": {
    "minVersion": "0.15.5"
  },
  "spm": {
    "modulesDir": ".sona_modules",
    "schema": 2
  },
  "version": "0.15.5"
}
```

Additional descriptive fields such as author, description, license, keywords,
and repository are retained by SPM.

Dependency names must be dotted Sona identifiers such as `my_pkg` or
`vendor.tools`. Slashes, backslashes, empty components, and parent traversal are
rejected.

## Local dependency sources

Dependencies may be regular local files or directories. An explicitly declared
sibling path such as `../my_pkg` remains supported for local development.
Absolute local paths are accepted when explicitly configured, although
`spm add` stores a normalized relative path when the platform permits it.

SPM rejects:

- missing or special-file sources;
- a source that contains the destination project;
- installed `.sona_modules` state used as a source;
- a source reached through a symlink; and
- any symlink inside a dependency directory.

SPM never downloads or extracts an archive in this release.

## Install location and containment

The default install directory is `.sona_modules/`.

Import resolution prefers:

- `.sona_modules/<name>.smod`; and
- `.sona_modules/<name>/__init__.smod`.

`spm.modulesDir` must be a relative, project-contained path. Absolute paths,
dot/parent components, drive paths, and existing symlink components are
rejected. Every derived package, staging, backup, modules, and lock destination
is checked against the resolved project boundary.

## Atomic installation

`spm install` processes the complete dependency set as one transaction:

```text
resolve -> validate -> stage -> verify -> atomic commit
```

All sources and declared integrity values are validated before live package
state changes. Packages are copied to a unique project-local staging tree and
hashed there. SPM then atomically replaces the modules tree and dependency lock.
If either commit fails, the previous modules and lock state are restored. A bad
dependency never leaves earlier dependencies partially installed.

SPM refuses to overwrite overlapping package targets such as separate
`package` and `package.child` directory dependencies.

## Deterministic dependency lock

New installs and `spm lock` write deterministic `sona.lock.json` schema 2:

```json
{
  "includeDev": false,
  "integrityAlgorithm": "sha256-tree-v2",
  "packages": {
    "my_pkg": {
      "installKind": "package-dir",
      "integrity": "sha256-...",
      "path": "../my_pkg",
      "sourceType": "directory",
      "version": "*"
    }
  },
  "schema": 2
}
```

The lock contains no generation or installation timestamps. Equivalent
manifest/source state produces identical bytes. `sha256-tree-v2` frames file
paths, sizes, and bytes deterministically and uses POSIX separators in package
metadata.

`spm verify` is read-only. It checks lock structure, manifest package-set
agreement, package presence, symlink safety, and installed content integrity.
Existing schema-1 dependency locks remain verifiable with their legacy
integrity algorithm, but all new writes use schema 2.

## Trust limits

Dependency hashes establish deterministic local content identity and tamper
detection after locking. They do not authenticate an author, signer, registry,
or machine. SPM does not add package data to the frozen Proof Mode schema-1
receipt. A future provenance design may associate deterministic package
identities with Proof Mode evidence without changing the claims of this release.
