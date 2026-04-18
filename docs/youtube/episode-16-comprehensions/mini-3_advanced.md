# Mini-Episode 16.3: Advanced Patterns 🎯

> Nested and dictionary comprehensions

---

## Nested Loops

```sona
// Pairs of numbers
let pairs = [(x, y) for x in range(3) for y in range(3)]
// [(0,0), (0,1), (0,2), (1,0), (1,1), (1,2), (2,0), (2,1), (2,2)]

// Multiplication table
let table = [f"{x}*{y}={x*y}" for x in range(1,4) for y in range(1,4)]
```

---

## Flatten Nested Lists

```sona
let matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

// Flatten to single list
let flat = [num for row in matrix for num in row]
// [1, 2, 3, 4, 5, 6, 7, 8, 9]
```

---

## Dictionary Comprehensions

Create dictionaries in one line:

```sona
// Basic syntax
{key: value for item in iterable}

// Examples:
let squares = {x: x**2 for x in range(5)}
// {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

let words = ["cat", "dog", "bird"]
let lengths = {w: len(w) for w in words}
// {"cat": 3, "dog": 3, "bird": 4}
```

---

## Dict Comprehension with Filter

```sona
let scores = {"Alice": 85, "Bob": 45, "Charlie": 72, "Diana": 91}

// Only passing scores (60+)
let passing = {name: score for name, score in scores.items() if score >= 60}
// {"Alice": 85, "Charlie": 72, "Diana": 91}
```

---

## Transform Dict Keys/Values

```sona
let prices = {"apple": 1.5, "banana": 0.75, "orange": 2.0}

// Apply discount
let sale = {item: price * 0.8 for item, price in prices.items()}
// {"apple": 1.2, "banana": 0.6, "orange": 1.6}

// Uppercase keys
let upper = {k.upper(): v for k, v in prices.items()}
// {"APPLE": 1.5, "BANANA": 0.75, "ORANGE": 2.0}
```

---

## Swap Keys and Values

```sona
let original = {"a": 1, "b": 2, "c": 3}
let swapped = {v: k for k, v in original.items()}
// {1: "a", 2: "b", 3: "c"}
```

---

## Set Comprehensions

Create sets (unique values):

```sona
let numbers = [1, 2, 2, 3, 3, 3, 4]
let unique_squares = {x**2 for x in numbers}
// {1, 4, 9, 16}  - no duplicates!
```

---

## Conditional Expression

```sona
// if-else in the expression
let numbers = [1, 2, 3, 4, 5]
let labels = ["even" if n % 2 == 0 else "odd" for n in numbers]
// ["odd", "even", "odd", "even", "odd"]

let values = [x if x > 0 else 0 for x in [-2, -1, 0, 1, 2]]
// [0, 0, 0, 1, 2]
```

---

## Best Practices

✅ Keep comprehensions **simple and readable**
✅ Use regular loops for **complex logic**
✅ Add **comments** if meaning isn't obvious
❌ Don't nest more than **2 levels deep**
