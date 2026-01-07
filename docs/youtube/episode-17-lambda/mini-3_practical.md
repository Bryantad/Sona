# Mini-Episode 17.3: Practical Lambda Uses 🎯

> Where lambdas really shine

---

## Sorting with Lambdas

Custom sort order with `key` parameter:

```sona
let words = ["banana", "pie", "apple", "watermelon"]

// Sort by length
let by_length = sorted(words, key=lambda w: len(w))
// ["pie", "apple", "banana", "watermelon"]

// Sort by last letter
let by_last = sorted(words, key=lambda w: w[-1])
// ["banana", "apple", "pie", "watermelon"]
```

---

## Sorting Objects

```sona
let students = [
    {"name": "Alice", "grade": 85},
    {"name": "Bob", "grade": 92},
    {"name": "Charlie", "grade": 78}
]

// Sort by grade
let by_grade = sorted(students, key=lambda s: s["grade"])
// Charlie (78), Alice (85), Bob (92)

// Sort by grade, highest first
let top_down = sorted(students, key=lambda s: -s["grade"])
// Bob (92), Alice (85), Charlie (78)
```

---

## Max/Min with Key

```sona
let products = [
    {"name": "Book", "price": 15},
    {"name": "Pen", "price": 2},
    {"name": "Laptop", "price": 999}
]

// Cheapest item
let cheapest = min(products, key=lambda p: p["price"])
// {"name": "Pen", "price": 2}

// Most expensive
let priciest = max(products, key=lambda p: p["price"])
// {"name": "Laptop", "price": 999}
```

---

## Default Values

```sona
let get_price = lambda item, default=0: item.get("price", default)

print(get_price({"price": 10}))    // 10
print(get_price({"name": "foo"}))  // 0 (default)
```

---

## Lambda in Data Processing

```sona
let data = [
    {"date": "2024-01-15", "amount": 100},
    {"date": "2024-01-10", "amount": 250},
    {"date": "2024-01-20", "amount": 75}
]

// Sort by date
let sorted_data = sorted(data, key=lambda x: x["date"])

// Total amount
let total = sum(map(lambda x: x["amount"], data))
// 425

// Average
let avg = total / len(data)
// 141.67
```

---

## Event Handlers

```sona
// Button click handlers
let buttons = {
    "add": lambda x: x + 1,
    "subtract": lambda x: x - 1,
    "double": lambda x: x * 2,
    "reset": lambda x: 0
}

let value = 5
value = buttons["double"](value)  // 10
value = buttons["add"](value)     // 11
```

---

## Quick Tip

**Lambda readability checklist:**

- [ ] Is it one simple expression?
- [ ] Would a name make it clearer?
- [ ] Can someone else understand it?

If you answered "no" to any, use a regular function!

```sona
// Too complex for lambda
let bad = lambda x: x if x > 0 else (-x if x < -10 else 0)

// Better as function
func normalize(x) {
    if x > 0 {
        return x
    } else if x < -10 {
        return -x
    }
    return 0
}
```
