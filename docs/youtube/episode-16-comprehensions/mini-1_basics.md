# Mini-Episode 16.1: Basic Comprehensions 🔄

> Transform data in one line

---

## What's a List Comprehension?

A **shortcut** for creating lists by transforming data.

```sona
// Old way (4 lines)
let squares = []
for x in range(5) {
    squares.append(x * x)
}

// New way (1 line!)
let squares = [x * x for x in range(5)]
```

Both create: `[0, 1, 4, 9, 16]`

---

## Basic Syntax

```sona
[expression for item in iterable]
```

- **expression**: What to do with each item
- **item**: Variable for current item
- **iterable**: What to loop through

---

## Examples

```sona
// Double each number
let numbers = [1, 2, 3, 4, 5]
let doubled = [n * 2 for n in numbers]
// [2, 4, 6, 8, 10]

// Get lengths of words
let words = ["cat", "elephant", "dog"]
let lengths = [len(w) for w in words]
// [3, 8, 3]

// Convert to uppercase
let names = ["alice", "bob"]
let upper = [n.upper() for n in names]
// ["ALICE", "BOB"]
```

---

## With Range

```sona
// First 10 squares
let squares = [i**2 for i in range(10)]
// [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

// Even numbers 0-20
let evens = [i for i in range(0, 21, 2)]
// [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
```

---

## Calling Functions

```sona
func process(x) {
    return x * 2 + 1
}

let results = [process(n) for n in range(5)]
// [1, 3, 5, 7, 9]
```

---

## When to Use

✅ **Use comprehensions for:**

- Simple transformations
- One-line operations
- Clear, readable code

❌ **Don't use for:**

- Complex logic (use regular loops)
- Multiple statements
- Side effects (printing, etc.)
