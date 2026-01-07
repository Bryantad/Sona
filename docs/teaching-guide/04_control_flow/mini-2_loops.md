# Mini-Episode 4.2: Loops

**Duration**: ~20 minutes  
**Difficulty**: ⭐ Beginner  
**Prerequisites**: [Mini-Episode 4.1: If/Else](mini-1_if_else.md)

---

## 📦 What You'll Learn

- [ ] While loops — repeat while condition is true
- [ ] For loops — iterate over collections
- [ ] Repeat loops — run a fixed number of times
- [ ] When to use each type

---

## 🎯 Why This Matters

Imagine printing "Hello" 1000 times by writing 1000 print statements. Loops let you write it once and repeat automatically. They're essential for:
- Processing lists of data
- Running game loops
- Waiting for user input
- Any repetitive task

---

## 🧩 Types of Loops

### While Loop

Repeats **while** a condition is true.

```sona
let count = 0
while count < 5 {
    print("Count: " + count)
    count = count + 1
}
```

**Output:**
```
Count: 0
Count: 1
Count: 2
Count: 3
Count: 4
```

### For Loop

Iterates over items in a collection.

```sona
let fruits = ["apple", "banana", "cherry"]
for fruit in fruits {
    print("I like " + fruit)
}
```

**Output:**
```
I like apple
I like banana
I like cherry
```

### Repeat Loop

Runs a specific number of times.

```sona
repeat 3 {
    print("Hello!")
}
```

**Output:**
```
Hello!
Hello!
Hello!
```

---

## 💻 Practical Examples

### Example 1: Countdown

```sona
let countdown = 5
while countdown > 0 {
    print(countdown + "...")
    countdown = countdown - 1
}
print("Liftoff! 🚀")
```

### Example 2: Sum Numbers

```sona
let numbers = [10, 20, 30, 40]
let total = 0

for num in numbers {
    total = total + num
}

print("Sum: " + total)  // Sum: 100
```

### Example 3: Find an Item

```sona
let names = ["Alice", "Bob", "Charlie", "Diana"]
let looking_for = "Charlie"
let found = false

for name in names {
    if name == looking_for {
        print("Found " + name + "!")
        found = true
    }
}

if not found {
    print("Not found")
}
```

---

## ⚠️ Infinite Loops

Be careful! If the condition never becomes false, the loop runs forever:

```sona
// ⚠️ DANGER: Infinite loop!
let x = 1
while x > 0 {
    print(x)
    x = x + 1    // x keeps growing, never becomes <= 0
}
```

**Always ensure your loop can terminate!**

---

## 🔬 Try It Yourself

### Exercise: Print a Pattern

```sona
// Use a loop to print:
// *
// **
// ***
// ****
// *****
```

<details>
<summary>Solution</summary>

```sona
let row = 1
while row <= 5 {
    let stars = ""
    let count = 0
    while count < row {
        stars = stars + "*"
        count = count + 1
    }
    print(stars)
    row = row + 1
}
```
</details>

---

## ✅ Checkpoint

1. **When does a while loop stop?**
   <details><summary>Answer</summary>When its condition becomes false</details>

2. **What loop is best for processing every item in a list?**
   <details><summary>Answer</summary>A for loop</details>

3. **What loop is best for running code exactly 10 times?**
   <details><summary>Answer</summary>repeat 10 { ... }</details>

---

## 🔗 Next Up

[Mini-Episode 4.3: Break & Continue](mini-3_break_continue.md)
