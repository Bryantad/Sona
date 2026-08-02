# Sona 0.15.4 Standard Library

The certified foundation has eleven public modules: `collection`, `date`,
`fs`, `http`, `io`, `json`, `math`, `random`, `stdin`, `string`, and `time`.
Application code imports those names directly. Modules named `native_*` are
private implementation details.

The authoritative machine-readable inventory is
`sona/stdlib/MANIFEST.json` (`sona.stdlib.manifest.schema-2`). Every export is
classified as `KEEP`, `RENAME`, `MOVE`, `DEPRECATE`, `REMOVE`, or `PRIVATE`,
and every foundation module records Python, Native Core, and standalone
support separately.

| Module | Responsibility | Python | Native/standalone |
| --- | --- | --- | --- |
| `collection` | General collection transforms | PASS | PARTIAL |
| `date` | Calendar dates | PASS | PASS |
| `fs` | Files and directories | PASS | PASS with explicit native capabilities |
| `http` | Bounded HTTP requests | PASS | UNSUPPORTED (`SONA-HTTP-005`) |
| `io` | Console output and flushing | PASS | PASS |
| `json` | JSON parse/stringify | PASS | PASS |
| `math` | Numeric helpers | PASS | PASS |
| `random` | Seeded random operations | PASS | PARTIAL; sequences are engine-specific |
| `stdin` | Console input | PASS | PASS |
| `string` | Text transforms | PASS | PASS |
| `time` | Clock, duration, and sleep | PASS | PASS |

Compatibility aliases remain quiet through 0.15.x. New code should prefer
canonical names such as `fs.read_text`, `json.parse`, `random.integer`, and
`string.starts_with`.

See [filesystem](fs.md), [HTTP](http.md), [data helpers](data.md),
[date/time](date-time.md), [console I/O](io-stdin.md), and
[runtime capabilities](runtime-capabilities.md).

The examples used for cross-engine certification are committed under
`tests/stdlib/conformance/` and run by
`tests/stdlib/run_0154_stdlib_conformance.py`.
