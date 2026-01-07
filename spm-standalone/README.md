# Sona Package Manager (SPM)

Offline-first package manager for Sona projects.

## What it does

- Creates a project manifest: `sona.json`
- Installs local-path dependencies into: `.sona_modules/`
- Generates a lock file with integrity hashes: `sona.lock.json`

Dependencies are **local paths only** (file or folder). No registry/network.

## Install (dev)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .
```

## Commands

```powershell
spm --help
spm init
spm add <name> <path>
spm add <name> <path> --dev
spm install
spm install --dev
spm lock
spm verify
spm catalog -o docs/catalog.json
```

## Notes

- `spm install` expects a `sona.json` in the current directory (or pass `--root`).
- The lock file records `sha256-...` integrity of the source path.
