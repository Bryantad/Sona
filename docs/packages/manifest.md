# Packages in Sona v0.10.1 (Local-Only)

v0.10.1 does **not** ship a public package registry.
It does ship the conventions needed to grow one later.

SPM is also available as a standalone tool repository: https://github.com/Bryantad/Spm

## Project manifest: `sona.json`

Created by:

- `spm init`
- `sona pkg init`

Minimal schema (v0.10):

```json
{
  "name": "my-project",
  "version": "0.10.1",
  "sona": { "minVersion": "0.10.1" },
  "dependencies": {
    "my_pkg": { "path": "../my_pkg" }
  },
  "devDependencies": {},
  "spm": { "schema": 2, "modulesDir": ".sona_modules" }
}
```

## Install location: `.sona_modules/`

Installed by:

- `spm install`

Import resolution prefers:

- `.sona_modules/<name>.smod`
- `.sona_modules/<name>/__init__.smod`

## Dependency sources

- **Local paths only** (file or directory). This avoids security + trust issues until a registry design exists.
