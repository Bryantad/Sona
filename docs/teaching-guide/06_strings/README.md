# Module 06: String Operations

## Overview
Strings are text—letters, words, sentences. This module teaches you how to manipulate, search, and format text like a pro.

**Target Audience:** Ages 12-55, neurodivergent-friendly  
**Prerequisites:** Modules 01-05  
**Duration:** 45-60 minutes

---

## Learning Objectives
By the end of this module, you will:
- Create and manipulate strings
- Search for text within strings
- Split and join strings
- Format strings with variables

---

## Why String Operations Matter

Almost every program works with text:
- Usernames and passwords
- Messages and notifications
- File names and paths
- Search queries
- Data from files and APIs

---

## Mini-Lessons in This Module

| Mini | Topic | Focus |
|------|-------|-------|
| [mini-1](mini-1_basics.md) | String Basics | Creating, accessing, common operations |
| [mini-2](mini-2_search_replace.md) | Search & Replace | Finding and replacing text |
| [mini-3](mini-3_formatting.md) | Formatting | String interpolation and templates |

---

## Key Vocabulary

| Term | Simple Definition | Example |
|------|-------------------|---------|
| **String** | Text data in quotes | `"Hello"` |
| **Concatenation** | Joining strings together | `"Hi" + " there"` |
| **Index** | Position of a character | `"abc"[0]` → `"a"` |
| **Substring** | Part of a string | `"Hello"[0:2]` → `"He"` |
| **Interpolation** | Inserting variables into text | `"Hi {name}"` |

---

## Quick Reference

```sona
let text = "Hello, World!"

// Length
print(text.length())      // 13

// Case conversion
print(text.upper())       // "HELLO, WORLD!"
print(text.lower())       // "hello, world!"

// Check content
print(text.starts_with("Hello"))  // true
print(text.contains("World"))     // true

// Find position
print(text.index_of("World"))     // 7

// Replace
print(text.replace("World", "Sona"))  // "Hello, Sona!"

// Split into list
let words = text.split(", ")      // ["Hello", "World!"]

// Join list into string
let joined = words.join(" - ")    // "Hello - World!"
```

---

## Common Mistakes

❌ **Forgetting strings are immutable**
```sona
let name = "alex"
name.upper()        // This doesn't change 'name'!
print(name)         // Still "alex"
```

✅ **Assign the result to a variable**
```sona
let name = "alex"
name = name.upper() // Now it's changed
print(name)         // "ALEX"
```

---

## Practice Challenges

### Challenge 1: Greeting
Create a variable with your name. Print "Hello, [NAME]!" with your name in uppercase.

### Challenge 2: Email Validator
Check if a string contains "@" and ".". If both, print "Valid email format".

### Challenge 3: Word Counter
Take a sentence and count how many words it has (hint: split by spaces).

---

## Self-Check Questions

1. How do you get the length of a string?
2. What does `.split(" ")` do?
3. How do you check if a string contains certain text?

<details>
<summary>Answers</summary>

1. `string.length()`
2. Splits the string into a list wherever there's a space
3. `string.contains("text")` returns true or false

</details>

---

## Next Steps
→ Continue to [Module 07: File I/O](../07_file_io/README.md)
