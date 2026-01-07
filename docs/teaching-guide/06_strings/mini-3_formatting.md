# Mini-Lesson 6.3: String Formatting

## Why Format Strings?

Building strings with variables can get messy:

```sona
// Ugly concatenation
let name = "Alex"
let age = 25
print("Hello, my name is " + name + " and I am " + age + " years old.")
```

String formatting makes this cleaner and easier to read.

---

## Method 1: String Interpolation (Recommended)

Use `{variable}` inside the string:

```sona
let name = "Alex"
let age = 25

print("Hello, my name is {name} and I am {age} years old.")
// Output: Hello, my name is Alex and I am 25 years old.
```

### Expressions Inside Braces

You can put calculations inside:

```sona
let price = 19.99
let quantity = 3

print("Total: ${price * quantity}")
// Output: Total: $59.97

let a = 5
let b = 3
print("{a} + {b} = {a + b}")
// Output: 5 + 3 = 8
```

---

## Method 2: The `format()` Function

Use placeholders `{}` and fill them in:

```sona
let template = "Hello, {}! You have {} messages."
let result = template.format("Alex", 5)
print(result)
// Output: Hello, Alex! You have 5 messages.
```

### Named Placeholders

```sona
let template = "Hello, {name}! You have {count} messages."
let result = template.format(name: "Alex", count: 5)
print(result)
```

---

## Formatting Numbers

### Decimal Places

```sona
let pi = 3.14159265359

print("Pi is approximately {pi:.2}")    // "Pi is approximately 3.14"
print("Pi is approximately {pi:.4}")    // "Pi is approximately 3.1416"
```

### Padding Numbers

```sona
let num = 42

print("{num:05}")   // "00042" (pad with zeros, width 5)
print("{num:5}")    // "   42" (pad with spaces, width 5)
```

---

## Formatting for Display

### Currency

```sona
let price = 1234.5

print("Price: ${price:.2}")
// Output: Price: $1234.50
```

### Percentages

```sona
let score = 0.875

print("Score: {score * 100:.1}%")
// Output: Score: 87.5%
```

### Alignment

```sona
let items = ["Apple", "Banana", "Cherry"]
let prices = [1.50, 0.75, 2.25]

for i, item in enumerate(items) {
    print("{item:<10} ${prices[i]:.2}")
}
```

**Output:**
```
Apple      $1.50
Banana     $0.75
Cherry     $2.25
```

| Code | Meaning |
|------|---------|
| `<10` | Left-align, width 10 |
| `>10` | Right-align, width 10 |
| `^10` | Center, width 10 |

---

## Building Complex Strings

### Multi-line Templates

```sona
let name = "Jordan"
let items = ["Widget", "Gadget", "Gizmo"]
let total = 45.99

let receipt = """
================================
         RECEIPT
================================
Customer: {name}

Items:
"""

for item in items {
    receipt = receipt + "  - {item}\n"
}

receipt = receipt + """
--------------------------------
Total: ${total:.2}
================================
"""

print(receipt)
```

---

## Escaping Braces

If you need a literal `{` or `}` in your string:

```sona
print("Use {{name}} for variables")
// Output: Use {name} for variables
```

---

## Practical Examples

### Example 1: Greeting Message

```sona
func greet(name, time_of_day) {
    return "Good {time_of_day}, {name}! Welcome back."
}

print(greet("Alex", "morning"))
// Output: Good morning, Alex! Welcome back.
```

### Example 2: Progress Bar

```sona
func progressBar(current, total, width = 20) {
    let percent = current / total
    let filled = (percent * width) as int
    let empty = width - filled
    
    let bar = "[" + "=" * filled + " " * empty + "]"
    return "{bar} {percent * 100:.1}%"
}

print(progressBar(7, 10))
// Output: [==============      ] 70.0%
```

### Example 3: Table Display

```sona
let students = [
    {"name": "Alice", "grade": 95},
    {"name": "Bob", "grade": 87},
    {"name": "Carol", "grade": 92}
]

print("{:<10} {:>5}".format("Name", "Grade"))
print("-" * 16)

for student in students {
    print("{student.name:<10} {student.grade:>5}")
}
```

**Output:**
```
Name       Grade
----------------
Alice         95
Bob           87
Carol         92
```

---

## Practice

### Exercise 1
Create a greeting that uses your name and current mood.

### Exercise 2
Format the number `3.14159` to show only 2 decimal places.

### Exercise 3
Create a receipt for 3 items with prices, showing each item and a total.

<details>
<summary>Exercise 3 Hint</summary>

```sona
let items = [
    {"name": "Coffee", "price": 4.50},
    {"name": "Muffin", "price": 3.25},
    {"name": "Cookie", "price": 2.00}
]

let total = 0
for item in items {
    print("{item.name}: ${item.price:.2}")
    total = total + item.price
}
print("Total: ${total:.2}")
```

</details>

---

## Summary

| Technique | Example | Result |
|-----------|---------|--------|
| Interpolation | `"Hi {name}"` | Variables inserted |
| Format | `"Hi {}".format("Alex")` | Placeholder filled |
| Decimals | `{x:.2}` | 2 decimal places |
| Padding | `{x:05}` | Zero-padded, width 5 |
| Left align | `{x:<10}` | Left in 10 chars |
| Right align | `{x:>10}` | Right in 10 chars |

---

## Module 06 Complete! 🎉

You've learned:
- ✅ String basics and manipulation
- ✅ Search and replace operations
- ✅ Professional string formatting

→ Next: [Module 07: File I/O](../07_file_io/README.md)
