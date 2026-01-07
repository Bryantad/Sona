# Module 08: Error Handling

## Overview
Errors happen. Good programmers plan for them. This module teaches you how to catch, handle, and recover from errors gracefully.

**Target Audience:** Ages 12-55, neurodivergent-friendly  
**Prerequisites:** Modules 01-07  
**Duration:** 40-50 minutes

---

## Learning Objectives
By the end of this module, you will:
- Understand different types of errors
- Use try/catch to handle errors
- Create helpful error messages
- Write defensive code that anticipates problems

---

## Why Error Handling Matters

Without error handling, your program crashes when something goes wrong. With it, your program can:
- Show friendly messages instead of scary errors
- Try alternative solutions
- Save data before closing
- Log problems for debugging

---

## Mini-Lessons in This Module

| Mini | Topic | Focus |
|------|-------|-------|
| [mini-1](mini-1_try_catch.md) | Try/Catch | Basic error handling |
| [mini-2](mini-2_error_types.md) | Error Types | Different kinds of errors |
| [mini-3](mini-3_defensive.md) | Defensive Coding | Preventing errors before they happen |

---

## Key Vocabulary

| Term | Simple Definition | Example |
|------|-------------------|---------|
| **Error** | Something went wrong | File not found |
| **Exception** | An error that can be caught | Division by zero |
| **Try** | Code that might fail | `try { risky_code() }` |
| **Catch** | Code to handle the error | `catch e { handle_it() }` |
| **Throw** | Deliberately cause an error | `throw "Invalid input"` |

---

## Quick Reference

```sona
// Basic try/catch
try {
    let result = riskyOperation()
    print(result)
} catch e {
    print("Error: " + e.message)
}

// With finally (always runs)
try {
    openFile()
    processData()
} catch e {
    print("Something went wrong")
} finally {
    closeFile()  // Always runs, error or not
}

// Throw your own error
func divide(a, b) {
    if b == 0 {
        throw "Cannot divide by zero"
    }
    return a / b
}
```

---

## Practice Challenges

### Challenge 1: Safe Division
Create a function that divides two numbers but returns 0 if division would fail.

### Challenge 2: User Input Validator
Write code that asks for a number and keeps asking until valid input is given.

### Challenge 3: File Reader
Create a function that reads a file, returning a default message if the file doesn't exist.

---

## Next Steps
→ Continue to [Module 09: Modules & Imports](../09_modules/README.md)
