# Sona v0.10.0 — Cognitive Preview Release Notes

Sona 0.10.0 is the first Cognitive Preview release. It makes intent, decision, trace, and cognitive scope metadata real and exportable.

This release introduces Sona's cognitive substrate. APIs and semantics may evolve throughout 0.10.x.

## Highlights

- Intent annotations, decision provenance, and cognitive scope boundaries
- Cognitive trace snapshots and explain_step artifacts
- Cognitive linting (runtime + LSP) with scope budget warnings
- Exportable cognitive reports via run_sona.py and VS Code
- Profile annotations for adhd/dyslexia/neurotypical

## CLI and VS Code

- Runner modes: `python run_sona.py <file.sona>` or `python run_sona.py run <file.sona>`
- Report export: `python run_sona.py report <file.sona> --format md|json --out <path>`
- VS Code: `Sona: Export Cognitive Report` creates `.sona/reports/<file>.cognitive_report.<fmt>`

## Known Gaps

- repeat-until parsing
- advanced match edge cases
- limited LSP diagnostics depth
- runtime coverage inconsistencies
