# Data, text, math, collections, and random values

`json.parse(source)` converts JSON text to Sona values. `json.stringify(value,
indent=nil)` emits deterministic key ordering; `indent` is `nil` or a
non-negative integer. `loads` and `dumps` remain compatibility aliases.

```sona
import json;
import string;
import math;
import collection;
import random;

let value = json.parse("{\"b\":2,\"a\":1}");
let source = json.stringify(value, 2);
let heading = string.upper("sona");
let first = collection.first([1, 2, 3]);

random.seed(42);
let roll = random.integer(1, 6);

if math.sqrt(81) == 9 {
    print(heading);
}
```

Prefer `string.starts_with`/`ends_with` and `random.integer`/`float`.
The compact spellings `startswith`, `endswith`, `randint`, and `random` remain
quiet aliases.

Seeded calls are repeatable within one engine. Python preserves its 0.15.3
generator, while Native Core uses a bounded internal generator, so 0.15.6
does not claim identical cross-engine random sequences.
