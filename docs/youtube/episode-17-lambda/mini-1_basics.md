# Mini-Episode 17.1: Lambda Basics ⚡

> Quick, anonymous functions

---

## What's a Lambda?

A **lambda** is a tiny function without a name.

```sona
// Regular function
func add(a, b) {
    return a + b
}

// Lambda version
let add = lambda a, b: a + b
```

Both do the same thing!

---

## Lambda Syntax

```sona
lambda parameters: expression
```

- **parameters**: Input values
- **expression**: What to return (single expression only!)

---

## Simple Examples

```sona
// One parameter
let double = lambda x: x * 2
print(double(5))  // 10

// Two parameters
let add = lambda a, b: a + b
print(add(3, 4))  // 7

// No parameters
let greet = lambda: "Hello!"
print(greet())  // Hello!
```

---

## When to Use Lambdas

Lambdas shine for:

- **Short operations** (one line)
- **Passing to functions** (like sort, map, filter)
- **One-time use** functions

---

## Lambda vs Regular Function

```sona
// Use lambda for simple stuff
let square = lambda x: x * x

// Use regular function for:
// - Multiple lines
// - Complex logic
// - Reusable code
// - Need docstrings

func complex_operation(x) {
    // Multiple steps
    let result = x * 2
    result = result + 10
    if result > 50 {
        result = 50
    }
    return result
}
```

---

## Common Patterns

```sona
// Get a property
let get_name = lambda user: user["name"]

// Check a condition
let is_adult = lambda age: age >= 18

// Format something
let format_price = lambda p: f"${p:.2f}"

print(format_price(9.99))  // $9.99
```
