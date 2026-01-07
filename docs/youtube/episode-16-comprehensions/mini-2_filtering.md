# Mini-Episode 16.2: Filtering 🔍

> Select only matching items

---

## Adding Conditions

Filter items with `if`:

```sona
[expression for item in iterable if condition]
```

---

## Basic Filtering

```sona
let numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

// Only even numbers
let evens = [n for n in numbers if n % 2 == 0]
// [2, 4, 6, 8, 10]

// Only odds
let odds = [n for n in numbers if n % 2 != 0]
// [1, 3, 5, 7, 9]

// Greater than 5
let big = [n for n in numbers if n > 5]
// [6, 7, 8, 9, 10]
```

---

## Filtering Strings

```sona
let words = ["apple", "banana", "ant", "cherry", "avocado"]

// Words starting with 'a'
let a_words = [w for w in words if w.startswith("a")]
// ["apple", "ant", "avocado"]

// Long words (6+ letters)
let long_words = [w for w in words if len(w) >= 6]
// ["banana", "cherry", "avocado"]
```

---

## Filter AND Transform

```sona
// Get squares of even numbers only
let numbers = [1, 2, 3, 4, 5, 6]
let result = [n**2 for n in numbers if n % 2 == 0]
// [4, 16, 36]

// Uppercase short words
let words = ["hi", "hello", "hey", "goodbye"]
let result = [w.upper() for w in words if len(w) <= 3]
// ["HI", "HEY"]
```

---

## Multiple Conditions

```sona
let numbers = range(1, 21)

// Divisible by 2 AND 3
let result = [n for n in numbers if n % 2 == 0 and n % 3 == 0]
// [6, 12, 18]

// Between 5 and 15
let result = [n for n in numbers if n > 5 and n < 15]
// [6, 7, 8, 9, 10, 11, 12, 13, 14]
```

---

## Practical Examples

```sona
// Remove empty strings
let items = ["hello", "", "world", "", "!"]
let cleaned = [s for s in items if s != ""]
// ["hello", "world", "!"]

// Get valid emails (simple check)
let emails = ["user@test.com", "invalid", "test@email.org"]
let valid = [e for e in emails if "@" in e and "." in e]
// ["user@test.com", "test@email.org"]

// Extract numbers from mixed list
let mixed = [1, "a", 2, "b", 3]
let nums = [x for x in mixed if type(x) == "int"]
// [1, 2, 3]
```
