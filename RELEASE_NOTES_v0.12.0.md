# Sona v0.12.0 Release Notes

**Release Date:** 2026-03-15
**Type:** Language-first boundary and packaging release

---

## Summary

v0.12.0 tightens Sona's public runtime boundary without changing its core identity. The release reduces default runtime-memory exports, introduces explicit `advanced` and `internal` surfaces, adds one low-risk nested `.smod` helper, and aligns package metadata across the core runtime, stdlib, and VS Code extension.

---

## Highlights

- `sona.runtime.memory` now presents the stable public model layer.
- Host/runtime kernels and storage moved behind `sona.runtime.memory.advanced`.
- Goal/checkpoint/orchestration helpers moved behind `sona.runtime.memory.internal`.
- Added `stdlib/utils/convert.smod` as a narrow nested stdlib quick win.
- Version metadata aligned to `0.12.0` across package and extension surfaces.

---

## Validation

- Native/runtime bundle: `93 passed`
- CLI/direct execution smoke: `1 passed`

---

## Release Identity

`0.12.0 introduces explicit runtime layering boundaries and keeps Sona language-first while moving host/runtime and agent orchestration surfaces behind advanced/internal modules.`