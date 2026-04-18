# Sona v0.9.7 – Release Plan

**Target Release Date:** Monday, October 27, 2025  
**Last Updated:** October 12, 2025

---

## 1. Release Objectives (Definition of Done)

- **Stdlib 30 → 40 modules** with backward-compatible namespaces.  
  **DoD:** `MANIFEST.json` lists ≥40 modules; `test_stdlib_40.py` green; API snippets build.
- **Two marquee features** for automation & data processing:  
  **A. Structured Errors** (typed errors + stack traces)  
  **B. Extensible Module Hooks** (plugin providers registry)  
  **DoD:** unit + acceptance tests, CLI pretty trace, `examples/plugins/demo_provider` runs.
- **Release tooling** (docs, CI, smoke):  
  **DoD:** CI matrix (Win/Linux, Py 3.12/3.13), smoke script green, `pdoc` site published.

---

## 2. Scope & Module Inventory

### 2.1 Target Module Additions (10 modules to reach 40 total)

| Priority | Module             | Type        | Minimal Public API (first cut)                                                                     |
| -------- | ------------------ | ----------- | -------------------------------------------------------------------------------------------------- |
| P0       | `collection.list`  | Reinstate   | `chunk(seq,n)`, `flatten(nested)`, `unique(seq)`, `window(seq,k,step=1)`                           |
| P0       | `collection.dict`  | Reinstate   | `safe_get(d,k,default)`, `merge(a,b,mode="prefer_right")`, `remap(d,map)`                          |
| P0       | `collection.set`   | Reinstate   | `union(a,b,…)`, `intersect(a,b,…)`, `diff(a,b)` (deterministic sorted output)                      |
| P0       | `collection.tuple` | Reinstate   | `zipn(*seqs)`, `unzip(seq_of_tuples)`, `head_tail(t)`                                              |
| P0       | `http`             | New         | `get(url,timeout=10,headers={})`, `post(url,data/json,…)` w/ retry policy                          |
| P0       | `cli`              | New         | `args()`, `prompt(label,secret=false)`, `echo(text,style=None)` (Windows-safe colors)              |
| P1       | `logging`          | New         | `logger(name).info/warn/error/debug(msg,context={})`; rotation hook to `perf.logging`              |
| P1       | `config`           | New         | `load(paths:[…], env_prefix="SONA_")` (merge INI/TOML/ENV + profile overlay)                       |
| P1       | `compression`      | New         | `zip(dir,out)`, `unzip(zip_file,dest)`, `gzip(path,out=None)`, `tar(dir,out,mode="gz")`            |
| P1       | `scheduler`        | New         | `every(spec, fn)`, `run_pending(now=None)`; spec accepts `@cron("*/5 * * * *")` or `@delay("10s")` |
| P2       | `net.socket`\*     | New (guard) | `tcp(host,port).send(bytes).recv(n)` (feature-flagged)                                             |

**Note:** If `net.socket` slips, swap in **`crypto.hmac`**: `hmac_sha256(key, data) → hex`.

**Namespace convention:** All reinstated helpers live under `collection.*` to avoid global collisions.

---

## 3. Feature Workstreams

### 3.1 Structured Errors

**Implementation:**

- **AST spans:** add `span=(start_line,start_col,end_line,end_col)` on nodes.
- **Runtime:** raise `SonaRuntimeError(type, message, span, call_stack:[frames])`.
- **CLI pretty trace:** source context with `^~~` caret; color only if TTY & not Windows "dumb" console.
- **Serialization:** `to_dict()` for logs/IDE integration.

**Sample internal structure (Python):**

```python
class SonaRuntimeError(Exception):
    def __init__(self, type_, message, span=None, call_stack=None):
        super().__init__(message)
        self.type = type_
        self.message = message
        self.span = span
        self.call_stack = call_stack or []

    def to_dict(self):
        return {"type": self.type, "message": self.message,
                "span": self.span, "stack": [f.to_dict() for f in self.call_stack]}
```

**Example CLI output:**

```
Error: TypeError: cannot add string and number
  at add_user (user.sona:12:9)
  11 |   let x = "7"
> 12 |   print(x + 3)
              ^~~ cannot add
```

### 3.2 Extensible Module Hooks (Providers)

**Implementation:**

- **Registry:** `sona.providers` (entry points in `pyproject.toml`).
- **Interface:**

```python
class NativeModuleProvider:
    name = "demo_provider"
    def modules(self) -> dict[str, object]:
        # return { "demo.hello": module_obj }
        ...
```

- **Loader:** `providers.load_all()` merges into stdlib namespace (no overwrite unless `--allow-provider-overwrite`).
- **Example plugin:** `examples/plugins/demo_provider` with `demo.hello.greet(name)` + tests.

**Sample provider entry point (`pyproject.toml`):**

```toml
[project.entry-points."sona.providers"]
demo_provider = "demo_provider:Provider"
```

**Sample provider code (`examples/plugins/demo_provider/demo_provider/hello.py`):**

```python
class Provider:
    name = "demo_provider"
    def modules(self):
        class Hello:
            def greet(self, name): return f"Hello, {name}!"
        return {"demo.hello": Hello()}
```

---

## 4. Repository Layout Changes

**New directories and files to add:**

```
sona/
  stdlib/
    collection/
      list.py
      dict.py
      set.py
      tuple.py
    http.py
    cli.py
    logging.py
    config.py
    compression.py
    scheduler.py
    # (optional) net/socket.py or crypto/hmac.py
  providers/
    __init__.py
    loader.py

examples/
  http/
    fetch_json.sona
  cli/
    hello_args.sona
  scheduler/
    cron_cleanup.sona
  plugins/demo_provider/
    pyproject.toml
    demo_provider/
      __init__.py
      hello.py

docs/
  api/0.9.7/       # generated by pdoc
  guides/modules/
    http.md
    cli.md
    logging.md
    config.md
    compression.md
    scheduler.md

tests/
  modules/
    test_collection_list.sona
    test_http.sona
    test_cli.sona
    test_logging.sona
    test_config.sona
    test_compression.sona
    test_scheduler.sona
  py/
    test_structured_errors.py
    test_providers_registry.py
  acceptance/
    test_stdlib_40.py

ci/
  smoke_win_linux.ps1
  smoke_unix.sh
```

---

## 5. Testing & CI Strategy

### 5.1 Acceptance & Unit Tests

- **Each module gets:** 3–5 `.sona` acceptance cases under `tests/modules/`.
- **Stdlib health:** `tests/acceptance/test_stdlib_40.py` validates presence + a sanity call for each new module.
- **Errors:** `tests/py/test_structured_errors.py` asserts `span` and stack shape.
- **Providers:** `tests/py/test_providers_registry.py` loads `demo_provider` and calls `demo.hello.greet`.

### 5.2 CI Matrix (Windows + Linux; Python 3.12, 3.13)

`.github/workflows/ci.yml` (snippet):

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        python: ["3.12", "3.13.0-beta.3"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: ${{ matrix.python }} }
      - run: pip install -e ".[dev]"
      - run: pytest -q
      - run: ./ci/smoke_unix.sh
        if: runner.os == 'Linux'
      - run: pwsh ci/smoke_win_linux.ps1
        if: runner.os == 'Windows'
```

### 5.3 Smoke Scripts (fast, no network)

- Parse + run `.sona` samples (`cli`, `http` with mocked provider, `scheduler` dry-run).
- Print "OK" tokens; CI greps for them.

**Example smoke script (`ci/smoke_unix.sh`):**

```bash
#!/bin/bash
set -euo pipefail
python -m sona --version
python -m sona run examples/cli/hello_args.sona -- --name Sona | grep "Sona" >/dev/null && echo "SMOKE_OK"
```

---

## 6. Documentation Requirements

- **API docs:** `pdoc -o docs/api/0.9.7 sona`
- **Module guides:** short "Try it" sections per module, e.g., `docs/guides/modules/http.md`:

````markdown
# http Module

```sona
import http
resp = http.get("https://api.example.com/health")
if resp.status == 200:
  print(resp.json.message)
```
````

- **CHANGELOG:** headline features + "How to opt into providers".
- **README:** update feature table (40 modules, structured errors, providers).

---

## 7. Release Timeline (Date-Accurate Schedule)

| Week        | Dates                   | Deliverables                                                                                                                                                                                                                                                            |
| ----------- | ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Week 0**  | Sun Oct 12              | Lock specs, open issues, branch `release/v0.9.7`                                                                                                                                                                                                                        |
| **Week 1**  | Mon Oct 13 – Sun Oct 19 | • Scaffold reinstated `collection.*` + tests<br>• Implement **`http`** (sync only), **`cli`**<br>• Land providers loader skeleton + sample plugin                                                                                                                       |
| **Week 2**  | Mon Oct 20 – Sun Oct 26 | • Implement **`logging`**, **`config`**, **`compression`**, **`scheduler`**<br>• Structured Errors end-to-end (AST spans → CLI pretty)<br>• Decide **`net.socket`** vs **`crypto.hmac`** by **Oct 22**<br>• CI matrix green; smoke scripts added; docs generation wired |
| **Release** | Mon Oct 27              | Tag `v0.9.7`, publish docs, announce                                                                                                                                                                                                                                    |

---

## 8. Implementation Issues (GitHub Backlog)

1. **[P0] Reintroduce collection helpers under `collection.*` namespaces**

   - [ ] Implement `collection.list` (`chunk`, `flatten`, `unique`, `window`)
   - [ ] Implement `collection.dict` (`safe_get`, `merge`, `remap`)
   - [ ] Implement `collection.set` (`union`, `intersect`, `diff`)
   - [ ] Implement `collection.tuple` (`zipn`, `unzip`, `head_tail`)
   - [ ] Tests in `tests/modules/…`

2. **[P0] `http` module (sync, retries, JSON)**

   - [ ] Abstraction over providers; fallback to stdlib `urllib`
   - [ ] `get`, `post`, simple `retry(count=2, backoff=0.2)`
   - [ ] Mock provider for tests; examples

3. **[P0] `cli` module**

   - [ ] `args()`, `prompt()`, `echo()` w/ style map; Windows-safe colors
   - [ ] Acceptance tests + example

4. **[P1] `logging` → `perf.logging` integration**

   - [ ] `logger(name)` with levels; rotation hook
   - [ ] JSONL emission path optional via env

5. **[P1] `config` merger**

   - [ ] INI/TOML/ENV merge; `profile` overlays; deterministic precedence
   - [ ] Tests: conflict resolution, env prefix

6. **[P1] `compression`**

   - [ ] zip/tar/gzip with streaming APIs
   - [ ] Cross-platform paths; tests with temp dirs

7. **[P1] `scheduler`**

   - [ ] `every("@cron(...)")`, `every("@delay(...)")`, `run_pending()`
   - [ ] Monotonic clock; cooperative docs

8. **[P0] Structured Errors**

   - [ ] AST span propagation
   - [ ] `SonaRuntimeError` shape + serialization
   - [ ] CLI renderer with context; tests

9. **[P0] Providers Registry (plugins)**

   - [ ] `sona.providers` loader; conflict policy flag
   - [ ] Demo plugin + test

10. **[P2] `net.socket` (feature-flag) OR `crypto.hmac` fallback**

    - [ ] Decision by Oct 22
    - [ ] Implement + tests

11. **[P0] CI Matrix + Smoke**

    - [ ] Add Win/Linux, Py 3.12/3.13
    - [ ] Smoke scripts & caching

12. **[P0] Docs & Site**
    - [ ] `pdoc` job, guides, examples
    - [ ] README/CHANGELOG updates

---

## 9. Release Validation Gates

Must pass all of the following before tagging v0.9.7:

- **Tests:** 100% pass; **coverage ≥ 85%** for new modules; no coverage regression overall.
- **Performance:** Structured error overhead ≤ **5%** on `bench_small.sona` (flag exists to disable spans).
- **Portability:** All modules pass on Windows & Linux.
- **Security:** `http` disallows `file://`, validates redirects opt-in, timeout default 10s.
- **Docs:** API site builds; examples run via smoke scripts.

---

## 10. Risks & Mitigations

| Risk                           | Impact | Mitigation                                                                              |
| ------------------------------ | ------ | --------------------------------------------------------------------------------------- |
| HTTP dependency creep          | Medium | Keep provider abstraction; stdlib fallback; pin optional deps                           |
| Scheduler timing accuracy      | Low    | Use `time.monotonic()`; document cooperative scheduling                                 |
| Error tracing performance cost | Medium | Span capture behind `SONA_SPANS=1` (default **on** in dev/CI, **auto-off** in `--fast`) |
| Plugin trust/security          | High   | Default deny overwrites; recommend signed wheels in docs                                |

---

## 11. Example Code Snippets

### Test Example (`tests/modules/test_http.sona`)

```sona
import http

resp = http.get("https://example.test/ok")
assert resp.status == 200
assert resp.json.ok == true
```

### Smoke Script Example (`ci/smoke_unix.sh`)

```bash
#!/bin/bash
set -euo pipefail
python -m sona --version
python -m sona run examples/cli/hello_args.sona -- --name Sona | grep "Sona" >/dev/null && echo "SMOKE_OK"
```

---

## 12. Alternative Paths (Time Crunch Scenarios)

If schedule pressure increases:

- **Option A:** Swap `net.socket` → `crypto.hmac` (saves 1 day), still hit 40 modules.
- **Option B:** Defer `scheduler` to v0.9.8; add `crypto.hmac` **and** small `fs.watch` module to stay at 40.
- **Option C:** Ship structured errors with spans **stored but not colored** (simplifies Windows terminals, saves 0.5 day).

---

## 13. Decision Log

| Date         | Decision                                        | Rationale                                                      |
| ------------ | ----------------------------------------------- | -------------------------------------------------------------- |
| Oct 12, 2025 | Keep 0.9.7 at 10 module additions (30→40 total) | Manageable scope; proven pipeline before scaling to 80 modules |
| Oct 12, 2025 | Defer 40 additional modules to 0.9.8+           | Quality over quantity; need stable tooling first               |
| TBD (Oct 22) | `net.socket` vs `crypto.hmac` final choice      | Depends on security review and feature-flag readiness          |

---

_Release plan approved and locked: October 12, 2025_
