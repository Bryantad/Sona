# Sona Language Reference

This document describes stable behavior available in Sona `0.15.0`.
It does not describe planned behavior.

Documentation truth rule: if this reference and runtime behavior disagree,
runtime behavior wins and this document must be corrected before release.

For CLI error output, see the
[`v0.14 diagnostics guide`](errors/v0.14-diagnostics.md).

## Comments

```sona
// This is a comment.
print("Comments are ignored by the runtime.");
```

## Literals

Stable literal forms include strings, numbers, booleans, `nil`, lists, and maps.

```sona
let name = "Sona";
let count = 3;
let active = true;
let missing = nil;
let items = ["read", "build", "run"];
let profile = {"language": "Sona"};
```

## Variables

Use `let` to bind a value.

```sona
let total = 2 + 3;
print(total);
```

Variables can be reassigned.

```sona
let count = 1;
count = count + 1;
print(count);
```

## Constants

Use `const` for values that should not be changed by user code.

```sona
const app_name = "Sona";
print(app_name);
```

## Functions and Returns

```sona
func add(a, b) {
    return a + b;
};

print(add(2, 3));
```

## Conditionals

Use `when` for expression-style branching.

```sona
let score = 82;
let grade = when {
    score >= 90 => "A";
    score >= 80 => "B";
    _ => "Keep practicing";
};

print(grade);
```

## Loops

`while` loops are stable for repeated work.

```sona
let count = 3;

while count > 0 {
    print(count);
    count = count - 1;
};
```

## Imports and Module Usage

Use `import module_name;` and call module functions with dot syntax.

```sona runnable
import string;

print(string.upper("sona"));
```

## Operators

Stable operators include:

| Category | Operators |
| --- | --- |
| Arithmetic | `+`, `-`, `*`, `/`, `%` |
| Comparison | `==`, `!=`, `<`, `<=`, `>`, `>=` |
| Boolean | `and`, `or`, `not` |
| Assignment | `=` |

## Scoping Rules

- Top-level variables are available after they are declared.
- Function parameters are available inside that function.
- Use a value only after it has been declared.

## Runtime-Backed Stdlib Note

Some stdlib modules are implemented through runtime-backed `.smod` contracts.
The user-facing import shape is still normal Sona module usage:

```sona runnable
import math;

print(math.sqrt(16));
```
