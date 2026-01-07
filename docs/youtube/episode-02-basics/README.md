# Episode 02: Variables & Types 📦

> Learn to store and use data in your programs

## Episode Overview

**Duration:** 15 minutes  
**Level:** Beginner  
**Goal:** Understand variables, data types, and basic operations

---

## Script Outline

### Intro (0:00 - 0:30)
"Welcome back! Last time we printed text. But what if we want to remember things? That's what variables are for!"

### What Are Variables? (0:30 - 2:30)
"A variable is like a labeled box:
- The label is the NAME
- The contents are the VALUE"

```sona
let age = 15
let name = "Alex"
```

"We use `let` to create a variable."

### Data Types (2:30 - 5:30)
```sona
// Numbers
let age = 25
let price = 19.99

// Text (Strings)
let name = "Sona"
let greeting = "Hello!"

// True/False (Booleans)
let isStudent = true
let hasPet = false
```

"Sona figures out the type automatically!"

### Using Variables (5:30 - 8:00)
```sona
let name = "Alex"
let age = 15

print("Hello, " + name)
print("You are " + age + " years old")
```

### Changing Variables (8:00 - 10:00)
```sona
let score = 0
print(score)  // 0

score = 10
print(score)  // 10

score = score + 5
print(score)  // 15
```

### Getting User Input (10:00 - 12:30)
```sona
let name = input("What is your name? ")
print("Hello, " + name + "!")
```

### Mini Project: Greeting Card (12:30 - 14:00)
```sona
let name = input("Your name: ")
let favoriteColor = input("Favorite color: ")

print("=== GREETING CARD ===")
print("Hello, " + name + "!")
print("Nice to know you like " + favoriteColor)
print("=====================")
```

### Outro (14:00 - 15:00)
- Recap: variables store data, types are automatic
- Challenge: Make a "About Me" program with 5 variables
- Next: Making decisions with if/else

---

## Mini-Episodes

1. [mini-1: Variables Explained](mini-1_variables.md) - 5 min
2. [mini-2: Data Types](mini-2_types.md) - 5 min
3. [mini-3: User Input](mini-3_input.md) - 5 min

---

## Code Examples

```sona
// Complete example from episode
let name = "Alex"
let age = 15
let hobby = "gaming"
let isStudent = true

print("=== About Me ===")
print("Name: " + name)
print("Age: " + str(age))
print("Hobby: " + hobby)
if isStudent {
    print("Status: Student")
}
```

---

## Keywords
variables, data types, strings, numbers, booleans, input, sona basics
