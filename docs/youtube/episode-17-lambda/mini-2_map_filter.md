# Mini-Episode 17.2: map & filter 🔄

> Transform lists with lambdas

---

## The map() Function

Apply a function to **every item** in a list:

```sona
let numbers = [1, 2, 3, 4, 5]

// Double everything
let doubled = list(map(lambda x: x * 2, numbers))
// [2, 4, 6, 8, 10]

// Square everything
let squared = list(map(lambda x: x ** 2, numbers))
// [1, 4, 9, 16, 25]
```

---

## Map vs Comprehension

```sona
// map way
let result = list(map(lambda x: x * 2, numbers))

// comprehension way
let result = [x * 2 for x in numbers]

// Both work! Use whichever is clearer.
```

---

## The filter() Function

Keep only items that **pass a test**:

```sona
let numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

// Keep only evens
let evens = list(filter(lambda x: x % 2 == 0, numbers))
// [2, 4, 6, 8, 10]

// Keep only > 5
let big = list(filter(lambda x: x > 5, numbers))
// [6, 7, 8, 9, 10]
```

---

## Filter with Strings

```sona
let words = ["apple", "a", "banana", "to", "cherry"]

// Only long words
let long = list(filter(lambda w: len(w) > 3, words))
// ["apple", "banana", "cherry"]

// Only starting with 'a'
let a_words = list(filter(lambda w: w.startswith("a"), words))
// ["apple", "a"]
```

---

## Chaining map and filter

```sona
let numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

// Get squares of even numbers
let result = list(map(
    lambda x: x ** 2,
    filter(lambda x: x % 2 == 0, numbers)
))
// [4, 16, 36, 64, 100]
```

---

## The reduce() Function

Combine all items into **one value**:

```sona
from functools import reduce

let numbers = [1, 2, 3, 4, 5]

// Sum all
let total = reduce(lambda a, b: a + b, numbers)
// 15

// Product of all
let product = reduce(lambda a, b: a * b, numbers)
// 120

// Find max
let maximum = reduce(lambda a, b: a if a > b else b, numbers)
// 5
```

---

## Real-World Example

```sona
let products = [
    {"name": "Apple", "price": 1.50, "in_stock": true},
    {"name": "Banana", "price": 0.75, "in_stock": false},
    {"name": "Orange", "price": 2.00, "in_stock": true}
]

// Get names of in-stock items
let available = list(map(
    lambda p: p["name"],
    filter(lambda p: p["in_stock"], products)
))
// ["Apple", "Orange"]
```
