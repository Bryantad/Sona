# Mini-Episode 8.1: String Methods 🔤

> Learn the most useful string functions

---

## What Are String Methods?

**Methods** are functions built into strings. They help you change and work with text.

Think of it like: A string comes with tools attached!

---

## Case Methods

```sona
// Change case
let name = "hello world"

print(name.upper())   // HELLO WORLD
print(name.lower())   // hello world
print(name.title())   // Hello World
```

**When to use:**
- `.upper()` - Comparing without case sensitivity
- `.lower()` - Normalizing input
- `.title()` - Formatting names/titles

---

## Split and Join

```sona
// Split string into list
let sentence = "apple,banana,cherry"
let fruits = sentence.split(",")
print(fruits)  // ["apple", "banana", "cherry"]

// Join list into string
let words = ["Hello", "World"]
let message = " ".join(words)
print(message)  // Hello World
```

**Think of it:**
- `split()` = Cut a string into pieces
- `join()` = Glue pieces together

---

## Strip Whitespace

```sona
let messy = "   hello   "
let clean = messy.strip()
print(clean)  // "hello"

// Also:
// .lstrip() - Remove left whitespace
// .rstrip() - Remove right whitespace
```

**Super useful for:** Cleaning user input!

---

## Find and Replace

```sona
let text = "I love dogs"

// Replace
let new_text = text.replace("dogs", "cats")
print(new_text)  // I love cats

// Check if contains
if "love" in text {
    print("Found it!")
}
```

---

## Practice Challenge

```sona
// Clean up user input
func clean_username(input) {
    return input.strip().lower()
}

let raw = "  JohnDoe123  "
print(clean_username(raw))  // johndoe123
```

---

## Quick Reference Card

| Method | What It Does | Example |
|--------|--------------|---------|
| `.upper()` | ALL CAPS | "hi" → "HI" |
| `.lower()` | all lowercase | "HI" → "hi" |
| `.strip()` | Remove spaces | " hi " → "hi" |
| `.split()` | Break apart | "a,b" → ["a","b"] |
| `.join()` | Combine | ["a","b"] → "a,b" |
| `.replace()` | Swap text | "cat" → "dog" |
