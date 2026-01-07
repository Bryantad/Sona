# Mini-Episode 2.2: Expressions

**Duration**: ~15 minutes  
**Difficulty**: ⭐ Beginner  
**Prerequisites**: [Mini-Episode 2.1: Variables](mini-1_variables.md)

---

## 📦 What You'll Learn

- [ ] What expressions are
- [ ] Math operators (+, -, *, /, %)
- [ ] String concatenation (joining text)
- [ ] Comparison operators (==, !=, <, >, etc.)
- [ ] Order of operations

---

## 🎯 Why This Matters

Expressions are how you make your code *do* things — calculate prices, compare scores, combine text, and make decisions. Without expressions, your program would just sit there with static values.

---

## 🧩 Core Concept

### What is an Expression?

**An expression is any code that produces a value.**

```
┌─────────────────────────────────────────────────┐
│ Expression          →    Evaluates To           │
│ ──────────────────       ─────────────          │
│ 5 + 3               →    8                      │
│ "Hello" + "World"   →    "HelloWorld"           │
│ 10 > 5              →    true                   │
│ age * 2             →    (depends on age)       │
└─────────────────────────────────────────────────┘
```

---

## 💻 Math Operators

### Basic Math

| Operator | Name | Example | Result |
|----------|------|---------|--------|
| `+` | Addition | `5 + 3` | `8` |
| `-` | Subtraction | `10 - 4` | `6` |
| `*` | Multiplication | `6 * 7` | `42` |
| `/` | Division | `15 / 3` | `5` |
| `%` | Modulo (remainder) | `17 % 5` | `2` |

### Code Example

```sona
let a = 10
let b = 3

print(a + b)   // 13
print(a - b)   // 7
print(a * b)   // 30
print(a / b)   // 3.333...
print(a % b)   // 1 (remainder of 10 ÷ 3)
```

### Understanding Modulo (%)

Modulo gives you the **remainder** after division.

```
17 ÷ 5 = 3 remainder 2
         ↑           ↑
      (ignored)   (17 % 5 = 2)
```

**Common uses:**
- Check if even: `number % 2 == 0`
- Check if odd: `number % 2 != 0`
- Wrap around: `position % max_length`

```sona
print(10 % 2)  // 0 (even number)
print(11 % 2)  // 1 (odd number)
print(7 % 3)   // 1
```

---

## 💻 String Operations

### Concatenation (Joining Text)

Use `+` to combine strings:

```sona
let first = "Hello"
let second = "World"
let combined = first + " " + second

print(combined)  // "Hello World"
```

### Mixing Strings and Numbers

```sona
let name = "Alex"
let age = 25

// Convert number to string for joining:
print(name + " is " + age + " years old")
// Output: Alex is 25 years old
```

---

## 💻 Comparison Operators

These return `true` or `false`:

| Operator | Meaning | Example | Result |
|----------|---------|---------|--------|
| `==` | Equal to | `5 == 5` | `true` |
| `!=` | Not equal | `5 != 3` | `true` |
| `<` | Less than | `3 < 5` | `true` |
| `>` | Greater than | `5 > 3` | `true` |
| `<=` | Less or equal | `5 <= 5` | `true` |
| `>=` | Greater or equal | `5 >= 3` | `true` |

### Code Example

```sona
let score = 85
let passing = 70

print(score > passing)   // true
print(score == 100)      // false
print(score >= 85)       // true
print(score != 0)        // true
```

### Chained Comparisons

Sona supports chained comparisons (like math notation):

```sona
let x = 5

print(1 < x < 10)   // true (x is between 1 and 10)
print(0 < x < 3)    // false (x is not between 0 and 3)
```

---

## 💻 Logical Operators

Combine true/false values:

| Operator | Meaning | Example | Result |
|----------|---------|---------|--------|
| `and` / `&&` | Both true | `true and false` | `false` |
| `or` / `\|\|` | At least one true | `true or false` | `true` |
| `not` / `!` | Opposite | `not true` | `false` |

### Code Example

```sona
let age = 25
let has_id = true

// Both conditions must be true
let can_enter = age >= 21 and has_id
print(can_enter)  // true

// At least one must be true
let free_entry = age < 12 or age > 65
print(free_entry)  // false

// Opposite
let is_minor = not (age >= 18)
print(is_minor)  // false
```

---

## 📊 Order of Operations

Sona follows standard math order (PEMDAS):

1. **P**arentheses `( )`
2. **E**xponents (not standard in Sona, use `math.pow()`)
3. **M**ultiplication & **D**ivision `* /`
4. **A**ddition & **S**ubtraction `+ -`
5. **C**omparisons `< > <= >= == !=`
6. **L**ogical `and or not`

### Examples

```sona
print(2 + 3 * 4)       // 14 (not 20!)
print((2 + 3) * 4)     // 20 (parentheses first)
print(10 - 4 - 2)      // 4 (left to right)
print(10 / 2 * 5)      // 25 (left to right)
```

---

## 🔬 Try It Yourself

### Exercise 1: Calculate a Total

```sona
// Calculate total price with tax
let price = 29.99
let quantity = 3
let tax_rate = 0.08

// Your code: calculate subtotal, tax, and total
let subtotal = ???
let tax = ???
let total = ???

print("Subtotal: $" + subtotal)
print("Tax: $" + tax)
print("Total: $" + total)
```

<details>
<summary>Solution</summary>

```sona
let price = 29.99
let quantity = 3
let tax_rate = 0.08

let subtotal = price * quantity
let tax = subtotal * tax_rate
let total = subtotal + tax

print("Subtotal: $" + subtotal)
print("Tax: $" + tax)
print("Total: $" + total)
```
</details>

### Exercise 2: Check Eligibility

```sona
let age = 16
let has_permit = true
let parent_present = true

// Can drive if: (age >= 16 AND has permit AND parent present)
// OR age >= 18
let can_drive = ???

print("Can drive: " + can_drive)
```

<details>
<summary>Solution</summary>

```sona
let age = 16
let has_permit = true
let parent_present = true

let can_drive = (age >= 16 and has_permit and parent_present) or age >= 18

print("Can drive: " + can_drive)  // true
```
</details>

---

## 🧠 Common Mistakes

### ❌ Mistake 1: Confusing `=` and `==`

```sona
if score = 100 {    // ❌ This assigns, doesn't compare!
    print("Perfect!")
}
```

**Fix**: Use `==` for comparison:
```sona
if score == 100 {   // ✅ Compares score to 100
    print("Perfect!")
}
```

### ❌ Mistake 2: Forgetting Order of Operations

```sona
let result = 100 - 50 * 2  // Result is 0, not 100!
```

**Fix**: Use parentheses when needed:
```sona
let result = (100 - 50) * 2  // Result is 100
```

### ❌ Mistake 3: Comparing Different Types

```sona
let input = "5"
if input == 5 {     // ❌ String "5" vs Number 5
    print("Match!")
}
```

**Fix**: Compare same types:
```sona
let input = "5"
if input == "5" {   // ✅ String to string
    print("Match!")
}
```

---

## ✅ Checkpoint

1. **What is `17 % 5`?**
   <details><summary>Answer</summary>2 (the remainder when 17 is divided by 5)</details>

2. **What does `"a" + "b" + "c"` produce?**
   <details><summary>Answer</summary>"abc"</details>

3. **What is `2 + 3 * 4`?**
   <details><summary>Answer</summary>14 (multiplication happens before addition)</details>

4. **What does `5 > 3 and 2 < 1` evaluate to?**
   <details><summary>Answer</summary>false (5 > 3 is true, but 2 < 1 is false, and true AND false = false)</details>

---

## 🎉 Module Complete!

You now understand:
- How to create and use variables
- Different data types
- Math, string, and logical operations
- Order of operations

---

## ➡️ Next Module

[Module 03: Functions](../03_functions/) — Reusable blocks of code
