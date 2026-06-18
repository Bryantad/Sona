# Sona Standard Library Reference

This reference documents the stable user-facing stdlib surface for Sona
`0.15.0`. The package may contain more modules, but this page is the usability
contract for new developers.

Documentation truth rule: if this reference and runtime behavior disagree,
runtime behavior wins and this document must be corrected before release. No
planned behavior is documented here.

Runnable examples are marked with `sona runnable`. Reference-only snippets are
not executed by the docs test.

## Quick Start

```sona
import math;
import string;
import json;
```

Use `math` for numeric helpers, `string` for text helpers, and `json` for
JSON-compatible data.

## Module Index

| Module | Purpose |
| --- | --- |
| `assert` | Run dedicated testing assertions. |
| `color` | Apply optional ANSI terminal styling. |
| `csv` | Parse, validate, and write comma-separated value data. |
| `date` | Work with ISO dates, calendar boundaries, and date differences. |
| `env` | Read and write process environment values. |
| `focus` | Track local in-memory focus sessions. |
| `format` | Produce deterministic human-readable output formatting. |
| `fs` | Inspect and manipulate filesystem paths. |
| `hashing` | Create deterministic digests for strings and byte-like data. |
| `intent` | Track local in-process intent notes. |
| `io` | Read from and write to text files. |
| `json` | Parse, validate, and serialize JSON-compatible data. |
| `log` | Use deterministic local logging helpers. |
| `math` | Use numeric helpers and common math operations. |
| `path` | Normalize, join, and inspect path strings. |
| `pipe` | Use functional pipeline helpers. |
| `string` | Transform and inspect text. |
| `time` | Read clocks, timestamps, and durations. |
| `url` | Parse, build, encode, and decode URL values. |
| `queue` | Use a Sona-authored FIFO queue. |
| `stack` | Use a Sona-authored LIFO stack. |
| `sort` | Sort values with Sona-authored loop implementations. |
| `search` | Find values in lists and strings with Sona-authored helpers. |
| `statistics` | Compute descriptive statistics in Sona. |
| `matrix` | Work with Sona-authored matrix map objects. |
| `graph` | Work with Sona-authored graph map objects. |
| `permissions` | Manage Sona-authored roles and permissions. |
| `random` | Use deterministic Sona RNG helpers with intrinsic seeding support. |
| `uuid` | Generate canonical UUID strings through a minimal intrinsic. |
| `secrets` | Generate secure tokens through minimal private intrinsics. |
| `password` | Hash and verify passwords with constant-time verification. |
| `jwt` | Encode and verify preview JWT-style tokens. |
| `crypto` | Use preview cryptographic wrappers over private intrinsics. |
| `profile` | Work with local cognitive-accessibility profile presets. |
| `simplify` | Simplify messages into plain-language text. |
| `breadcrumb` | Track local in-memory workflow breadcrumbs. |
| `flow` | Score local workflow flow and suggest next steps. |
| `explain` | Produce deterministic runtime explanations. |
| `pace` | Format output with local pacing preferences. |
| `affirm` | Produce factual success and milestone messages. |
| `chunk` | Chunk lists, text, steps, and checkpoints. |
| `timer` | Use local monotonic focus timers. |
| `noise` | Filter local event noise. |
| `tone` | Normalize message tone. |
| `readability` | Check text and identifier readability. |
| `linewidth` | Wrap and check line width. |
| `mirror` | Explain similar symbols and pairs. |
| `chunk_read` | Navigate chunked reading sections. |
| `contract` | Run explicit runtime contract checks. |
| `boundary` | Apply local permission boundaries. |
| `routine` | Define and step through local routines. |
| `strict` | Run opt-in strict checks. |
| `certainty` | Track local assumptions and uncertainty notes. |
| `sensory` | Apply low-stimulation text transformations. |
| `guardian` | Guard a project with local snapshots, drift detection, quarantine, rollback, and audit history. |

## csv

### Status
Stable

### Purpose
Parse, validate, and write comma-separated value data.

### Functions
`parse(csv_data, options=nil)`, `parse_file(file_path, options=nil)`,
`stringify(records, options=nil)`, `write_file(file_path, records, options=nil)`,
`validate(csv_data, options=nil)`, `extract_fields(records, field_names)`.

### Example
```sona runnable
import csv;

let data = "name,score\nAda,10";
print(csv.validate(data));
```

### Notes
Runtime-backed parsing behavior is provided through the native stdlib bridge.

## date

### Status
Stable

### Purpose
Work with ISO dates, calendar boundaries, and date differences.

### Functions
`today(tz=nil)`, `yesterday(tz=nil)`, `tomorrow(tz=nil)`,
`parse(value, tz=nil)`, `format_iso(value, tz=nil)`,
`diff(start, end, unit=nil, absolute=nil, tz=nil)`.

### Example
```sona runnable
import date;

print(date.today());
```

### Notes
Date results can vary by current day and timezone.

## env

### Status
Stable

### Purpose
Read and write process environment values.

### Functions
`get(key, fallback=nil)`, `get_bool(key, fallback=nil)`,
`get_int(key, fallback=nil)`, `exists(key)`, `set(key, value)`,
`delete(key)`, `keys(prefix=nil)`, `parse_dotenv(content)`.

### Example
```sona runnable
import env;

print(env.get("SONA_DOCS_EXAMPLE", "not set"));
```

### Notes
Environment changes are process-local for the current run.

## fs

### Status
Stable

### Purpose
Inspect and manipulate filesystem paths.

### Functions
`read(path, encoding=nil)`, `write(path, content, encoding=nil)`,
`exists(path)`, `is_file(path)`, `is_dir(path)`, `list_dir(path)`,
`mkdir(path, parents=nil, exist_ok=nil)`, `remove(path, recursive=nil)`.

### Example
```sona runnable
import fs;

print(fs.exists("examples/hello.sona"));
```

### Notes
Examples should avoid depending on files created by previous runs.

## hashing

### Status
Stable

### Purpose
Create deterministic digests for strings and byte-like data.

### Functions
`md5(data)`, `sha1(data)`, `sha256(data)`, `sha512(data)`,
`sha3_256(data)`, `sha3_512(data)`, `hash(data)`, `checksum(data, algorithm=nil)`.

### Example
```sona runnable
import hashing;

print(hashing.sha256("sona"));
```

### Notes
Use `sha256` or stronger algorithms for new examples.

## io

### Status
Stable

### Purpose
Read from and write to text files.

### Functions
`input(prompt=nil)`, `write_file(path, content)`, `read_file(path)`.

### Example
```sona runnable
import io;

io.write_file("docs_io_example.txt", "hello");
print(io.read_file("docs_io_example.txt"));
```

### Notes
`input` is interactive and should not be used in automated examples.

## json

### Status
Stable

### Purpose
Parse, validate, and serialize JSON-compatible data.

### Functions
`loads(text, options=nil)`, `load(path, options=nil)`,
`dumps(value, options=nil)`, `dump(value, path, options=nil)`,
`pretty(value)`, `is_valid(text, options=nil)`, `validate(text, options=nil)`.

### Example
```sona runnable
import json;

let data = {"language": "Sona"};
let text = json.dumps(data);
print(json.is_valid(text));
```

### Notes
Use `dumps` and `loads` for in-memory examples.

## math

### Status
Stable

### Purpose
Perform arithmetic and common numeric operations.

### Functions
`add(a, b)`, `subtract(a, b)`, `multiply(a, b)`, `divide(a, b)`,
`sqrt(x)`, `pow(x, y)`, `clamp(value, lower, upper)`, `round(value, ndigits=nil)`.

### Example
```sona runnable
import math;

print(math.sqrt(16));
```

### Notes
Constants such as `PI`, `TAU`, and `E` are available on the module.

## memory

### Status
Preview

### Purpose
Access the runtime memory integration when configured.

### Functions
`search(query, opts=nil)`, `record(content, opts=nil)`,
`get_trace(trace_id)`, `reflect(input=nil, opts=nil)`.

### Example
```sona runnable
import memory;

print("memory module imported");
```

### Notes
Memory operations may require runtime configuration. The runnable example only
validates that the module imports.

## path

### Status
Stable

### Purpose
Build, normalize, and inspect filesystem paths.

### Functions
`join(a, b=nil, c=nil, d=nil, e=nil, f=nil, g=nil, h=nil)`,
`normalize(path)`, `basename(path)`, `dirname(path)`, `extension(path)`,
`is_absolute(path)`, `is_relative(path)`, `resolve(base, target)`.

### Example
```sona runnable
import path;

print(path.join("examples", "hello.sona"));
```

### Notes
Path formatting follows the current operating system.

## string

### Status
Stable

### Purpose
Transform and inspect text.

### Functions
`upper(value)`, `lower(value)`, `title(value)`, `trim(value, chars=nil)`,
`contains(value, substring, options=nil)`, `starts_with(value, prefix, options=nil)`,
`ends_with(value, suffix, options=nil)`, `split(value, delimiter=nil, options=nil)`.

### Example
```sona runnable
import string;

print(string.upper("sona"));
```

### Notes
String helpers coerce common values to text where the runtime supports it.

## time

### Status
Stable

### Purpose
Work with timestamps, ISO time strings, and time differences.

### Functions
`now(timespec=nil, tz=nil)`, `utcnow(timespec=nil)`, `timestamp()`,
`from_timestamp(value, timespec=nil, tz=nil)`, `parse(value, tz=nil, timespec=nil)`,
`format_iso(value, timespec=nil, tz=nil)`, `diff(start, end, unit=nil, absolute=nil)`.

### Example
```sona runnable
import time;

print(time.now());
```

### Notes
Time results vary by clock and timezone.

## Cognitive Profile Presets

### Status
Stable

### Purpose
`profile` selects local cognitive-accessibility support presets. Presets are
explicit user choices, not diagnoses, and they do not persist state by default.

### Functions
`available()`, `activate(name)`, `activate_many(names)`, `current()`,
`configure(options)`, `reset()`.

### Runtime Effects

- `cross-profile`: guided pacing and conservative flow thresholds.
- `adhd`: guided pacing, focused noise filtering, and lower flow-switch
  tolerance.
- `dyslexia`: guided pacing, 72-character line width, and shorter identifier
  readability threshold.
- `autism`: guided pacing, strict checks enabled, and low-stimulation sensory
  text transformation enabled.
- `low-stimulation`: low-stimulation pacing, minimal noise filtering, and
  sensory text transformation enabled.
- `custom`: no automatic preset changes; explicit `configure` options apply.

`profile.current()` reports the active preset names, preserved options, a
runtime snapshot for `pace`, `noise`, `linewidth`, `readability`, `strict`,
`sensory`, and `flow`, plus `local_only: true` and `persistent: false`.

### Notes
Known runtime options are validated before mutation. Unknown options are
preserved for compatibility but do not change runtime state.

## Sona-Native Foundation Modules

Sona `0.15.0` moves the public foundation for `queue`, `stack`, `sort`,
`search`, `statistics`, `matrix`, `graph`, and `permissions` into
`stdlib/*.smod`. These modules are authored in Sona and should not depend on
regular Python stdlib modules for their public implementation.

`hashing`, `random`, `uuid`, `secrets`, `password`, `jwt`, and `crypto` are
Sona-authored wrappers over a small private intrinsic set. `crypto.encrypt_simple`
is preview/legacy obfuscation only and is not production encryption.
