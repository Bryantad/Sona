# Mini-Episode 2.1: Variables

**Duration**: ~15 minutes  
**Difficulty**: ⭐ Beginner  
**Prerequisites**: [Module 01: Introduction](../01_introduction/)

---

## 📦 What You'll Learn

- [ ] What variables are and why we need them
- [ ] How to create variables with `let`
- [ ] Different types of data you can store
- [ ] Rules for naming variables

---

## 🎯 Why This Matters

Imagine trying to cook without any bowls or containers — you'd have nowhere to put ingredients while working. Variables are your containers in programming. They let you:
- Store information to use later
- Give meaningful names to values
- Change values as your program runs

---

## 🧩 Core Concept

### What is a Variable?

**A variable is a named container that holds a value.**

```
┌─────────────────────────────────────────────────┐
│                                                 │
│   Variable Name        Value Inside             │
│   ─────────────        ───────────────          │
│                                                 │
│   ┌─────────┐         ┌─────────────┐           │
│   │  age    │    →    │     25      │           │
│   └─────────┘         └─────────────┘           │
│                                                 │
│   ┌─────────┐         ┌─────────────┐           │
│   │  name   │    →    │   "Alex"    │           │
│   └─────────┘         └─────────────┘           │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Creating Variables in Sona

Use the `let` keyword:

```sona
let age = 25
let name = "Alex"
let is_student = true
```

**Breaking it down:**
- `let` — Tells Sona "I'm creating a variable"
- `age` — The name you choose
- `=` — Puts the value into the variable
- `25` — The value being stored

---

## 💻 Code Examples

### Example 1: Basic Variables

```sona
let greeting = "Hello"
let year = 2025
let is_awesome = true

print(greeting)
print(year)
print(is_awesome)
```

**Output:**
```
Hello
2025
true
```

### Example 2: Using Variables Together

```sona
let first_name = "Taylor"
let last_name = "Swift"
let full_name = first_name + " " + last_name

print("Welcome, " + full_name + "!")
```

**Output:**
```
Welcome, Taylor Swift!
```

### Example 3: Changing Variables

```sona
let score = 0
print("Starting score: " + score)

score = 10
print("After level 1: " + score)

score = score + 5
print("After bonus: " + score)
```

**Output:**
```
Starting score: 0
After level 1: 10
After bonus: 15
```

---

## 📊 Data Types

Sona has several types of data:

| Type | What It Is | Examples |
|------|------------|----------|
| **String** | Text in quotes | `"Hello"`, `"42"`, `""` |
| **Number** | Integers or decimals | `42`, `3.14`, `-10` |
| **Boolean** | True or false | `true`, `false` |
| **Null** | Nothing/empty | `null` |

### How to Tell Types Apart

```sona
let text = "42"      // String (has quotes)
let number = 42      // Number (no quotes)
let yes = true       // Boolean (special word)
let nothing = null   // Null (special word)
```

> ⚠️ **Important**: `"42"` (string) and `42` (number) are different!
> - `"42" + "8"` → `"428"` (joins text)
> - `42 + 8` → `50` (adds numbers)

---

## 📝 Naming Rules

### ✅ Valid Variable Names

```sona
let name = "Alex"           // ✅ lowercase
let firstName = "Alex"      // ✅ camelCase
let first_name = "Alex"     // ✅ snake_case
let player1 = "Alex"        // ✅ numbers ok (not at start)
let _private = "secret"     // ✅ underscore ok
```

### ❌ Invalid Variable Names

```sona
let 1player = "Alex"        // ❌ can't start with number
let first-name = "Alex"     // ❌ no hyphens
let first name = "Alex"     // ❌ no spaces
let let = "Alex"            // ❌ can't use keywords
```

### 💡 Naming Tips

| Style | Example | When to Use |
|-------|---------|-------------|
| `snake_case` | `user_name` | Most Sona code |
| `camelCase` | `userName` | Also acceptable |
| `UPPER_CASE` | `MAX_SIZE` | Constants that never change |

---

## 🔬 Try It Yourself

### Exercise 1: Create a Profile

**Goal**: Store information about yourself in variables

```sona
// Create these variables about yourself:
let my_name = "???"
let my_age = ???
let favorite_color = "???"
let likes_pizza = ???  // true or false

// Print them out:
print("Name: " + my_name)
print("Age: " + my_age)
print("Favorite color: " + favorite_color)
print("Likes pizza: " + likes_pizza)
```

### Exercise 2: Swap Values

**Goal**: Swap the values of two variables

```sona
let a = "first"
let b = "second"

// Your code here to swap them...

print(a)  // Should print: second
print(b)  // Should print: first
```

<details>
<summary>Click for hint</summary>
You need a third variable to hold one value temporarily!
</details>

<details>
<summary>Click for solution</summary>

```sona
let a = "first"
let b = "second"

let temp = a
a = b
b = temp

print(a)  // second
print(b)  // first
```
</details>

---

## 🧠 Common Mistakes

### ❌ Mistake 1: Using Before Creating

```sona
print(score)      // ❌ Error: score doesn't exist yet
let score = 100
```

**Fix**: Create the variable first:
```sona
let score = 100
print(score)      // ✅ Works
```

### ❌ Mistake 2: Forgetting Quotes for Text

```sona
let name = Alex   // ❌ Error: Alex is not defined
```

**Fix**: Add quotes around text:
```sona
let name = "Alex" // ✅ Works
```

### ❌ Mistake 3: Wrong Type Operations

```sona
let age = "25"
let next_year = age + 1  // ❌ Can't add number to string
```

**Fix**: Use the right type:
```sona
let age = 25             // Number, not string
let next_year = age + 1  // ✅ Works: 26
```

---

## ✅ Checkpoint

1. **What keyword creates a variable in Sona?**
   <details><summary>Answer</summary>let</details>

2. **What's the difference between `"100"` and `100`?**
   <details><summary>Answer</summary>"100" is a string (text), 100 is a number. They behave differently in operations.</details>

3. **Can a variable name start with a number?**
   <details><summary>Answer</summary>No. Variable names must start with a letter or underscore.</details>

4. **What does this output?**
   ```sona
   let x = 5
   x = x + 3
   print(x)
   ```
   <details><summary>Answer</summary>8 (starts at 5, adds 3)</details>

---

## 🔗 Next Up

[Mini-Episode 2.2: Expressions](mini-2_expressions.md) — Math and combining values
