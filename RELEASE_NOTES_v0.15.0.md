# Sona 0.15.0 - Cognitive Runtime and Guardian Resilience Layer

Sona `0.15.0` adds the cognitive-accessibility runtime foundation and the
Guardian local resilience layer. The release keeps parser and grammar behavior
unchanged.

## Highlights

- 55 cognitive-accessibility modules are represented in the canonical stdlib
  manifest:
  - 21 stable accessibility modules.
  - 34 experimental accessibility modules.
- Experimental accessibility modules are runtime-backed and local-only by
  default. Session-state, adaptive, or history behavior requires explicit local
  opt-in with `{ "experimental_accessibility": true }`.
- Guardian adds project-root confined local resilience:
  - SHA-256 inventory.
  - Trusted local config hash.
  - PARG graph.
  - Drift detection.
  - Snapshot creation.
  - Diff.
  - Quarantine.
  - Rollback with post-rollback verification.
  - Circuit breaker.
  - JSON and plain-language reports.
  - Local audit history.
- `python -m sona probe stdlib` now uses static manifest metadata and remains
  under the 5 second performance gate on the reference machine.

## Safety Notes

- Guardian mutation tests use temporary fixture projects outside the source
  repository.
- Guardian never intentionally writes outside the initialized project root.
- Guardian excludes `.git`, virtual environments, caches, build output, secrets,
  and its own `.sona/guardian` state by default.
- Guardian does not execute newly introduced validation commands from a modified
  `sona.guard.json`; it uses the trusted policy recorded at `sona guard init`.
- Automatic healing is not silent. The default behavior is detect, report, and
  recommend. Mutating recovery requires explicit `sona guard heal --apply`.

## Experimental Scope

Advanced signing and provenance remain interface-ready or deferred unless backed
by existing local primitives:

- Signed release manifests.
- External trust anchors.
- Key rotation.
- Provenance attestations.
- Secure update metadata.

## Validation

The release ledger is maintained in
`docs/release/0.15.0-validation-ledger.md`. The module inventory is documented
in `docs/release/0.15.0-module-matrix.md`.

Required final validation:

```text
python -m pytest -q tests
python tools/validate_release_metadata.py --version 0.15.0
python -m sona --version
python -m sona --help
python -m sona probe stdlib
python -m sona probe stdlib --category utility
python -m sona probe stdlib --category accessibility
python -m sona probe stdlib --category resilience
python -m sona probe stdlib --stability experimental
python -m sona probe accessibility
python -m sona probe guardian
python tools/run_examples.py
powershell -ExecutionPolicy Bypass -File scripts\release_hardening.ps1
```

Guardian CLI mutation smoke tests must run against temporary fixture projects,
not the repository root.

Final validation results:

- `python -m pytest -q tests`: 114 passed, 2 warnings.
- `python -m sona probe stdlib`: static manifest mode, median 0.139s across
  three final runs.
- `python tools/run_examples.py`: 9 examples passed.
- `python -m twine check --strict dist-pypi-0.15.0/*`: passed.
- Wheel and sdist smoke installs imported Sona from
  `C:\Users\yungd\AppData\Local\Temp\sona-release-hardening-0.15.0`, outside
  the source repository.

## Artifact Hashes

```text
sona_lang-0.15.0-py3-none-any.whl
Size: 552413 bytes
SHA-256: e541c222c64820bd49018633e6173529360f6aec3bcdd2e884deae7b500c3c5a

sona_lang-0.15.0.tar.gz
Size: 458750 bytes
SHA-256: 249059de41bd56935d7f0829e7659a54fdeb09a725e87c443cf03c9fd46f8f08
```
