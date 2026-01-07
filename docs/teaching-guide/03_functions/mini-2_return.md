# Mini-Episode 3.2: Return Values

**Duration**: ~15 minutes  
**Difficulty**: ⭐ Beginner  
**Prerequisites**: [Mini-Episode 3.1: Parameters](mini-1_params.md)

---

## 📦 What You'll Learn

- [ ] What return values are
- [ ] How to use the `return` keyword
- [ ] Difference between `print` and `return`
- [ ] Using returned values in your code

---

## 🎯 Why This Matters

So far, our functions have just printed things. But what if you want a function to calculate something and give you the answer back? That's what `return` does — it lets functions produce values you can use.

---

## 🧩 Core Concept

### What is a Return Value?

**A return value is data that a function sends back to wherever it was called.**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  func add(a, b) {                                       │
│      return a + b    ← Sends value BACK                 │
│  }                                                      │
│                                                         │
│  let result = add(5, 3)  ← Catches the return value     │
│  print(result)           ← 8                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Print vs Return

| `print()` | `return` |
|-----------|----------|
| Shows text on screen | Sends value back to caller |
| For humans to see | For code to use |
| Can't use the value later | Can store and use the value |

---

## 💻 Basic Return Example

### Without Return (printing)

```sona
func add_print(a, b) {
    print(a + b)    // Shows result, but can't use it
}

add_print(5, 3)     // Output: 8
let x = add_print(5, 3)  // x is null! Can't capture printed values
```

### With Return

```sona
func add(a, b) {
    return a + b    // Sends result back
}

let result = add(5, 3)   // result is now 8
print(result)            // Output: 8
print(result * 2)        // Output: 16 (we can use it!)
```

---

## 💻 Practical Examples

### Example 1: Calculator Functions

```sona
func add(a, b) {
    return a + b
}

func subtract(a, b) {
    return a - b
}

func multiply(a, b) {
    return a * b
}

func divide(a, b) {
    return a / b
}

// Using them together:
let x = add(10, 5)           // 15
let y = multiply(x, 2)       // 30
let z = subtract(y, 10)      // 20

print("Final answer: " + z)  // Final answer: 20
```

### Example 2: Temperature Converter

```sona
func celsius_to_fahrenheit(c) {
    return (c * 9 / 5) + 32
}

func fahrenheit_to_celsius(f) {
    return (f - 32) * 5 / 9
}

let hot_day = celsius_to_fahrenheit(35)
print("35°C = " + hot_day + "°F")   // 35°C = 95°F

let cold_day = fahrenheit_to_celsius(32)
print("32°F = " + cold_day + "°C")  // 32°F = 0°C
```

### Example 3: Building Complex Logic

```sona
func calculate_area(width, height) {
    return width * height
}

func calculate_perimeter(width, height) {
    return 2 * (width + height)
}

func describe_rectangle(width, height) {
    let area = calculate_area(width, height)
    let perimeter = calculate_perimeter(width, height)
    
    return "Area: " + area + ", Perimeter: " + perimeter
}

let info = describe_rectangle(5, 3)
print(info)  // Area: 15, Perimeter: 16
```

---

## 💻 Using Returns in Expressions

Returned values can be used directly in expressions:

```sona
func double(n) {
    return n * 2
}

func square(n) {
    return n * n
}

// Use in expressions directly
print(double(5) + 10)           // 20 (10 + 10)
print(square(4))                 // 16

// Chain function calls
print(double(double(3)))         // 12 (double(6))
print(square(double(2)))         // 16 (square(4))

// Use in conditions
if double(5) > 8 {
    print("Greater!")            // This prints
}
```

---

## 💻 Early Returns

You can return from anywhere in a function:

```sona
func check_age(age) {
    if age < 0 {
        return "Invalid age"      // Exits early
    }
    
    if age < 18 {
        return "Minor"
    }
    
    return "Adult"                // Only reached if not minor
}

print(check_age(-5))   // Invalid age
print(check_age(12))   // Minor
print(check_age(25))   // Adult
```

---

## 📊 Return Types

Functions can return any type:

```sona
// Return a number
func get_pi() {
    return 3.14159
}

// Return a string
func get_greeting() {
    return "Hello, World!"
}

// Return a boolean
func is_even(n) {
    return n % 2 == 0
}

// Return a calculation
func get_discount(price, percent) {
    return price * (percent / 100)
}

print(get_pi())              // 3.14159
print(get_greeting())        // Hello, World!
print(is_even(4))            // true
print(get_discount(100, 20)) // 20
```

---

## 🔬 Try It Yourself

### Exercise 1: Max Function

**Goal**: Create a function that returns the larger of two numbers

```sona
// Create func max(a, b) that returns the larger number

// Test cases:
// max(5, 3) should return 5
// max(2, 8) should return 8
// max(4, 4) should return 4
```

<details>
<summary>Solution</summary>

```sona
func max(a, b) {
    if a > b {
        return a
    }
    return b
}

print(max(5, 3))  // 5
print(max(2, 8))  // 8
print(max(4, 4))  // 4
```
</details>

### Exercise 2: Grade Calculator

**Goal**: Create a function that returns a letter grade for a score

```sona
// Create func get_grade(score) that returns:
// "A" for 90-100
// "B" for 80-89
// "C" for 70-79
// "D" for 60-69
// "F" for below 60

// Test cases:
// get_grade(95) → "A"
// get_grade(82) → "B"
// get_grade(55) → "F"
```

<details>
<summary>Solution</summary>

```sona
func get_grade(score) {
    if score >= 90 {
        return "A"
    }
    if score >= 80 {
        return "B"
    }
    if score >= 70 {
        return "C"
    }
    if score >= 60 {
        return "D"
    }
    return "F"
}

print(get_grade(95))  // A
print(get_grade(82))  // B
print(get_grade(55))  // F
```
</details>

### Exercise 3: Using Multiple Functions

**Goal**: Build a tip calculator using multiple functions

```sona
// Create:
// func calculate_tip(bill, percent) - returns tip amount
// func calculate_total(bill, tip) - returns bill + tip
// func split_bill(total, people) - returns amount per person

// Then calculate: $85 bill, 20% tip, split 4 ways
```

<details>
<summary>Solution</summary>

```sona
func calculate_tip(bill, percent) {
    return bill * (percent / 100)
}

func calculate_total(bill, tip) {
    return bill + tip
}

func split_bill(total, people) {
    return total / people
}

let bill = 85
let tip = calculate_tip(bill, 20)        // 17
let total = calculate_total(bill, tip)    // 102
let per_person = split_bill(total, 4)     // 25.5

print("Bill: $" + bill)
print("Tip: $" + tip)
print("Total: $" + total)
print("Per person: $" + per_person)
```
</details>

---

## 🧠 Common Mistakes

### ❌ Mistake 1: Forgetting to Return

```sona
func add(a, b) {
    a + b         // ❌ Calculates but doesn't return!
}

let result = add(5, 3)
print(result)     // null (nothing was returned)
```

**Fix**: Add the `return` keyword:
```sona
func add(a, b) {
    return a + b  // ✅ Now it returns the value
}
```

### ❌ Mistake 2: Code After Return

```sona
func greet(name) {
    return "Hello, " + name
    print("This never runs!")    // ❌ Unreachable code
}
```

**Why**: `return` exits the function immediately. Code after it never runs.

### ❌ Mistake 3: Confusing Print and Return

```sona
func get_double(n) {
    print(n * 2)      // ❌ Prints, doesn't return
}

let x = get_double(5)  // Prints 10, but x is null!
let y = x + 1          // ❌ Error: can't add null + 1
```

**Fix**: Use return when you need the value:
```sona
func get_double(n) {
    return n * 2       // ✅ Returns the value
}

let x = get_double(5)  // x is 10
let y = x + 1          // y is 11 ✅
```

---

## ✅ Checkpoint

1. **What does `return` do?**
   <details><summary>Answer</summary>Sends a value back from the function to wherever it was called</details>

2. **What's the difference between `print(5)` and `return 5`?**
   <details><summary>Answer</summary>print shows 5 on screen but doesn't give it back to use. return sends 5 back so you can store it or use it in expressions.</details>

3. **What does this function return?**
   ```sona
   func mystery(x) {
       if x > 10 {
           return "big"
       }
       return "small"
   }
   mystery(5)
   ```
   <details><summary>Answer</summary>"small" (5 is not > 10, so it skips to the second return)</details>

4. **Can you have code after a return statement?**
   <details><summary>Answer</summary>You can write it, but it will never run — return exits the function immediately</details>

---

## 🎉 Module Complete!

You now understand:
- How to create reusable functions
- How to pass data in with parameters
- How to get data back with return values

---

## ➡️ Next Module

[Module 04: Control Flow](../04_control_flow/) — Making decisions and loops
