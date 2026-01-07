# Mini-Episode 4.3: Break & Continue

**Duration**: ~10 minutes  
**Difficulty**: ⭐ Beginner  
**Prerequisites**: [Mini-Episode 4.2: Loops](mini-2_loops.md)

---

## 📦 What You'll Learn

- [ ] `break` — exit a loop early
- [ ] `continue` — skip to the next iteration
- [ ] When to use each

---

## 🧩 Core Concepts

### Break — Exit Immediately

`break` stops the loop completely and continues with code after the loop.

```sona
let i = 0
while i < 10 {
    if i == 5 {
        break       // Stop when i reaches 5
    }
    print(i)
    i = i + 1
}
print("Done")
```

**Output:**
```
0
1
2
3
4
Done
```

### Continue — Skip This Iteration

`continue` skips the rest of the current iteration and goes to the next one.

```sona
let i = 0
while i < 5 {
    i = i + 1
    if i == 3 {
        continue    // Skip printing when i is 3
    }
    print(i)
}
```

**Output:**
```
1
2
4
5
```

---

## 💻 Practical Examples

### Example 1: Find First Match and Stop

```sona
let items = ["book", "pen", "gold", "paper"]

for item in items {
    if item == "gold" {
        print("Found treasure!")
        break    // Stop searching
    }
    print("Checking: " + item)
}
```

**Output:**
```
Checking: book
Checking: pen
Found treasure!
```

### Example 2: Skip Invalid Data

```sona
let values = [10, -5, 20, -3, 15]
let total = 0

for val in values {
    if val < 0 {
        continue   // Skip negative numbers
    }
    total = total + val
}

print("Sum of positives: " + total)  // 45
```

---

## ✅ Checkpoint

1. **What does `break` do?**
   <details><summary>Answer</summary>Exits the loop immediately, no more iterations</details>

2. **What does `continue` do?**
   <details><summary>Answer</summary>Skips the rest of the current iteration and moves to the next one</details>

---

## 🎉 Module Complete!

You now control program flow with conditions and loops!

---

## ➡️ Next Module

[Module 05: Collections](../05_collections/) — Lists and Dictionaries
