# Mini-Episode 4.1: If/Else Statements

**Duration**: ~15 minutes  
**Difficulty**: ⭐ Beginner  
**Prerequisites**: [Module 03: Functions](../03_functions/)

---

## 📦 What You'll Learn

- [ ] How to make decisions with `if`
- [ ] How to handle alternatives with `else`
- [ ] How to chain conditions with `elif`
- [ ] Nested conditions

---

## 🎯 Why This Matters

Real programs need to make decisions:
- "If the password is correct, log in"
- "If the user is under 18, show parental warning"
- "If the cart is empty, disable checkout"

Without conditions, programs can only do one thing. With them, they can respond to anything.

---

## 🧩 Core Concept

### Basic If Statement

```sona
if condition {
    // code runs if condition is true
}
```

**Example:**
```sona
let age = 20

if age >= 18 {
    print("You can vote!")
}
```

### If/Else

```sona
if condition {
    // runs if true
} else {
    // runs if false
}
```

**Example:**
```sona
let age = 16

if age >= 18 {
    print("You can vote!")
} else {
    print("Too young to vote")
}
```

### If/Elif/Else Chain

```sona
if condition1 {
    // first check
} elif condition2 {
    // second check
} elif condition3 {
    // third check
} else {
    // none matched
}
```

**Example:**
```sona
let score = 85

if score >= 90 {
    print("A - Excellent!")
} elif score >= 80 {
    print("B - Good job!")
} elif score >= 70 {
    print("C - Passing")
} else {
    print("Need improvement")
}
// Output: B - Good job!
```

---

## 💻 Practical Examples

### Example 1: Login Check

```sona
let entered_password = "secret123"
let correct_password = "secret123"

if entered_password == correct_password {
    print("Login successful!")
    print("Welcome back!")
} else {
    print("Wrong password")
    print("Please try again")
}
```

### Example 2: Price Calculator with Discounts

```sona
let total = 150
let discount = 0

if total >= 200 {
    discount = 20
} elif total >= 100 {
    discount = 10
} elif total >= 50 {
    discount = 5
}

let final_price = total - discount
print("Original: $" + total)
print("Discount: $" + discount)
print("Final: $" + final_price)
```

### Example 3: Multiple Conditions with `and`/`or`

```sona
let age = 25
let has_license = true
let is_sober = true

if age >= 16 and has_license and is_sober {
    print("You may drive")
} else {
    print("You cannot drive")
}
```

---

## 🔬 Try It Yourself

### Exercise: Build a Simple Game Choice

```sona
let player_choice = "attack"
let enemy_health = 100

// If player chooses "attack", reduce enemy health by 20
// If player chooses "defend", print "You raise your shield"
// If player chooses "run", print "You fled the battle"
// Otherwise, print "Invalid action"

// Your code here...

print("Enemy health: " + enemy_health)
```

<details>
<summary>Solution</summary>

```sona
let player_choice = "attack"
let enemy_health = 100

if player_choice == "attack" {
    enemy_health = enemy_health - 20
    print("You attack!")
} elif player_choice == "defend" {
    print("You raise your shield")
} elif player_choice == "run" {
    print("You fled the battle")
} else {
    print("Invalid action")
}

print("Enemy health: " + enemy_health)
```
</details>

---

## ✅ Checkpoint

1. **When does the `else` block run?**
   <details><summary>Answer</summary>When the if condition (and all elif conditions) are false</details>

2. **Can you have multiple `elif` blocks?**
   <details><summary>Answer</summary>Yes, as many as you need</details>

3. **What's the output?**
   ```sona
   let x = 5
   if x > 10 {
       print("big")
   } elif x > 3 {
       print("medium")
   } else {
       print("small")
   }
   ```
   <details><summary>Answer</summary>"medium" — x is not > 10, but it is > 3</details>

---

## 🔗 Next Up

[Mini-Episode 4.2: Loops](mini-2_loops.md) — Repeating code
