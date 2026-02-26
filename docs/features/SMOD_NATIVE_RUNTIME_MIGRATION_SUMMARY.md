# Sona v0.10.3 Native `.smod` Runtime Migration Summary

## Date
- February 19, 2026

## Objective
- Execute must-have stdlib modules as true native `.smod` runtime modules.
- Avoid Python wrapper pass-throughs for migrated modules where feasible.
- Keep bridge loading opt-in (only for modules that explicitly require `__native__`).

## Release Scope (v0.10.3)
- New native module: `stdlib/uuid.smod`
- Final hard native module migration: `stdlib/regex.smod`
- Safe digest module added: `stdlib/hashing.smod` (`runtime_backend = "smod-bridge"`)
- Previously migrated native modules retained:
  - `stdlib/queue.smod`
  - `stdlib/stack.smod`
  - `stdlib/random.smod`
- Validation updates in `tests/test_smod_native_modules.py`
- Packaging updates to include native `stdlib/*.smod` files in release artifacts

## Final Result
- Six priority modules now run through the `.smod` runtime path:
  - `queue`
  - `stack`
  - `random`
  - `uuid`
  - `regex`
  - `hashing`
- Native module contract is explicit via:
  - `module_format = "smod-runtime"` (all migrated modules)
  - `runtime_backend = "smod"` (bridge-free modules)
  - `runtime_backend = "smod-bridge"` (hashing safety/correctness path)
- Focused migration tests pass for all six modules.

## Runtime/Architecture Foundation

### 1) `.smod` loader bridge behavior
File: `sona/interpreter.py`

- `.smod` load path checks whether source actually needs native bridge calls.
- Pure modules load and execute without requiring `native_*` Python wrappers.
- Bridge is only required when `__native__` usage is present.

### 2) Return propagation correctness
File: `sona/interpreter.py`

- `return` now propagates correctly through nested block execution in function calls.
- This fixed wrong-return behavior that surfaced during module migration.

### 3) Dict-backed method/property dispatch stability
File: `sona/ast_nodes.py`

- Property access prefers dictionary keys before Python attributes.
- Method dispatch works on dict-backed objects and injects receiver correctly.
- This enables natural APIs like `q.enqueue("x")` and `s.pop()`.

### 4) Parser ambiguity reduction
File: `sona/grammar.lark`

- Ambiguous atom alternatives were reduced in favor of postfix-based call/index parsing.
- This lowered call/index misparse frequency during `.smod` migration work.

## Native Modules in v0.10.3

### 5) `queue` (native `.smod`)
File: `stdlib/queue.smod`

- Full queue API implemented in `.smod`.
- Includes standard queue operations and priority helpers.
- Marked with native runtime metadata.

### 6) `stack` (native `.smod`)
File: `stdlib/stack.smod`

- Full stack API implemented in `.smod`.
- Includes push/pop/peek/search plus helper transforms.
- Uses parser-safe expression patterns where needed.

### 7) `random` (native `.smod`)
File: `stdlib/random.smod`

- Deterministic seeded PRNG utilities implemented in `.smod`.
- Covers integer/random selection helpers and common distributions.
- Seed behavior is validated for reproducibility.

### 8) `uuid` (new in v0.10.3, native `.smod`)
File: `stdlib/uuid.smod`

- Implemented as bridge-free `.smod` module with runtime metadata.
- API includes:
  - `v4`, `uuid4`
  - `v1`, `uuid1`
  - `v3`, `v5`, `uuid5`
  - `nil`
  - `is_valid`
  - `generate`
  - `short`
  - `to_bytes`
  - `from_bytes`
  - namespace constants (`NAMESPACE_DNS`, `NAMESPACE_URL`, `NAMESPACE_OID`, `NAMESPACE_X500`)
- Implementation favors parser/runtime-safe constructs to avoid known expression edge cases.

### 9) `regex` (final hard native module in v0.10.3)
File: `stdlib/regex.smod`

- Migrated to a bridge-free native `.smod` implementation with runtime metadata.
- API includes:
  - `compile`
  - `match`
  - `fullmatch`
  - `search`
  - `test`
  - `find_all` / `findall`
  - `replace`
  - `split`
  - `escape`
- Current implementation is regex-lite and prioritized for `.smod` runtime reliability over full Python `re` parity.
- Explicitly avoids Python `__native__` wrapper calls.

### 10) `hashing` (safe digest `.smod` module in v0.10.3)
File: `stdlib/hashing.smod`

- Added as `.smod` module with explicit runtime metadata.
- API includes:
  - `sha256`, `hash`, `digest`, `checksum`
  - compatibility helpers: `md5`, `sha1`, `sha512`, `sha3_256`, `sha3_512`, `blake2b`, `hmac_sha256`
- Uses `runtime_backend = "smod-bridge"` for cryptographic correctness and compatibility.
- SHA-256 golden vector checks were added to focused migration tests.

## Validation

### 11) Focused migration tests
- `python -m pytest tests/test_smod_native_modules.py -q`
- Result: `6 passed`
- Coverage now includes dedicated `uuid`, `regex`, and `hashing` module tests in `tests/test_smod_native_modules.py`.

### 12) Runtime script verification
- `python run_sona.py test_experimental_modules.sona`
- `python run_sona.py test_stdlib_regex.sona`
- `python run_sona.py test_stdlib_data.sona`
- `python run_sona.py test_all_30_imports.sona`
- `test_all_30_imports.sona` reports `30/30` imports successful.

## Known Constraints
- Earley parser complexity still requires defensive coding style in some `.smod` modules.
- Full functional suite still includes unrelated non-migration failures in other modules; this release is scoped to native `.smod` migration stability.

## v0.10.3 Summary
- Native `.smod` runtime migration is now established across six must-have modules.
- `regex` remains the final hard bridge-free module; `hashing` is the safe digest module added with bridge-backed correctness.
- This is the documented cutoff for the `v0.10.3` native module milestone.
