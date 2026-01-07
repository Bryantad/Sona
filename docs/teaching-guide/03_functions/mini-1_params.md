# Mini-Episode 3.1: Parameters

**Duration**: ~15 minutes  
**Difficulty**: ⭐ Beginner  
**Prerequisites**: [Module 02: Basics](../02_basics/)

---

## 📦 What You'll Learn

- [ ] What a function is
- [ ] How to define (create) a function
- [ ] How to call (use) a function
- [ ] What parameters are and how to use them

---

## 🎯 Why This Matters

Imagine writing the same code 100 times with slight changes. Functions let you write it once and reuse it forever. They're the foundation of organized, maintainable code.

---

## 🧩 Core Concept

### What is a Function?

**A function is a named, reusable block of code.**

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  func greet(name) {         ← Function DEFINITION        │
│      print("Hello, " + name)                             │
│  }                                                       │
│                                                          │
│  greet("Alex")              ← Function CALL              │
│                                                          │
│  Output: Hello, Alex                                     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### The Two Steps

1. **Define** the function (teach the computer what to do)
2. **Call** the function (tell the computer to do it)

---

## 💻 Creating Your First Function

### Step 1: Define It

```sona
func say_hello() {
    print("Hello, World!")
}
```

**Breaking it down:**
- `func` — Keyword that starts a function definition
- `say_hello` — The name you choose
- `()` — Parentheses (for parameters, empty for now)
- `{ }` — The code block that runs when called

### Step 2: Call It

```sona
say_hello()   // Output: Hello, World!
say_hello()   // Output: Hello, World!
say_hello()   // Output: Hello, World!
```

One definition → unlimited calls!

---

## 💻 Adding Parameters

Parameters let you pass information INTO a function.

### One Parameter

```sona
func greet(name) {
    print("Hello, " + name + "!")
}

greet("Alex")     // Hello, Alex!
greet("Jordan")   // Hello, Jordan!
greet("Sam")      // Hello, Sam!
```

**How it works:**
1. When you call `greet("Alex")`
2. `"Alex"` gets put into the `name` parameter
3. Inside the function, `name` equals `"Alex"`

### Multiple Parameters

```sona
func introduce(name, age) {
    print(name + " is " + age + " years old")
}

introduce("Alex", 25)      // Alex is 25 years old
introduce("Jordan", 30)    // Jordan is 30 years old
```

**Order matters!** The first argument goes to the first parameter, second to second, etc.

---

## 📊 Parameters vs Arguments

These terms are often confused:

| Term | Definition | Example |
|------|------------|---------|
| **Parameter** | Variable in the function definition | `name` in `func greet(name)` |
| **Argument** | Value passed when calling | `"Alex"` in `greet("Alex")` |

```sona
func greet(name) {    // ← name is a PARAMETER
    print("Hi " + name)
}

greet("Alex")         // ← "Alex" is an ARGUMENT
```

---

## 💻 Practical Examples

### Example 1: Price Calculator

```sona
func show_price(item, price) {
    print(item + ": $" + price)
}

show_price("Coffee", 4.99)
show_price("Sandwich", 8.50)
show_price("Cookie", 2.00)
```

**Output:**
```
Coffee: $4.99
Sandwich: $8.50
Cookie: $2.00
```

### Example 2: Repeated Messages

```sona
func repeat_message(message, times) {
    let i = 0
    while i < times {
        print(message)
        i = i + 1
    }
}

repeat_message("Hello!", 3)
```

**Output:**
```
Hello!
Hello!
Hello!
```

### Example 3: Game Action

```sona
func attack(attacker, defender, damage) {
    print(attacker + " attacks " + defender + " for " + damage + " damage!")
}

attack("Hero", "Goblin", 15)
attack("Goblin", "Hero", 8)
```

**Output:**
```
Hero attacks Goblin for 15 damage!
Goblin attacks Hero for 8 damage!
```

---

## 🔬 Try It Yourself

### Exercise 1: Create a Greeter

**Goal**: Make a function that greets someone by name

```sona
// Define a function called 'welcome' that takes a 'name' parameter
// and prints "Welcome to Sona, [name]!"

// Call it with your name
// Call it with a friend's name
```

<details>
<summary>Solution</summary>

```sona
func welcome(name) {
    print("Welcome to Sona, " + name + "!")
}

welcome("Alex")
welcome("Jordan")
```
</details>

### Exercise 2: Rectangle Info

**Goal**: Make a function that shows rectangle dimensions

```sona
// Create a function 'show_rectangle' that takes width and height
// and prints: "Rectangle: [width] x [height]"

// Test with: 10 x 5, then 3 x 7
```

<details>
<summary>Solution</summary>

```sona
func show_rectangle(width, height) {
    print("Rectangle: " + width + " x " + height)
}

show_rectangle(10, 5)
show_rectangle(3, 7)
```
</details>

---

## 🧠 Common Mistakes

### ❌ Mistake 1: Forgetting to Call the Function

```sona
func greet(name) {
    print("Hello, " + name)
}

// Nothing happens! You defined it but never called it.
```

**Fix**: Add a call:
```sona
greet("Alex")  // Now it runs!
```

### ❌ Mistake 2: Wrong Number of Arguments

```sona
func add(a, b) {
    print(a + b)
}

add(5)        // ❌ Error: missing argument for 'b'
add(5, 3, 1)  // ❌ Error: too many arguments
```

**Fix**: Match parameter count:
```sona
add(5, 3)     // ✅ Correct: 8
```

### ❌ Mistake 3: Arguments in Wrong Order

```sona
func subtract(a, b) {
    print(a - b)
}

subtract(3, 10)  // Prints -7, not 7!
```

**Fix**: Think about order:
```sona
subtract(10, 3)  // Prints 7 ✅
```

---

## ✅ Checkpoint

1. **What keyword defines a function in Sona?**
   <details><summary>Answer</summary>func</details>

2. **What's the difference between a parameter and an argument?**
   <details><summary>Answer</summary>A parameter is the variable in the function definition. An argument is the actual value passed when calling the function.</details>

3. **What happens if you define a function but never call it?**
   <details><summary>Answer</summary>Nothing — the code inside never runs.</details>

4. **How many arguments does this call need? `func calculate(x, y, z)`**
   <details><summary>Answer</summary>3 arguments</details>

---

## 🔗 Next Up

[Mini-Episode 3.2: Return Values](mini-2_return.md) — Getting data back from functions
