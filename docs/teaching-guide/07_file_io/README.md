# Module 07: File I/O

## Overview
Programs need to save and load data. This module teaches you how to read from and write to files—essential for any real application.

**Target Audience:** Ages 12-55, neurodivergent-friendly  
**Prerequisites:** Modules 01-06  
**Duration:** 45-60 minutes

---

## Learning Objectives
By the end of this module, you will:
- Read text from files
- Write and append to files
- Handle file errors safely
- Work with different file formats

---

## Why File I/O Matters

Without files, your data disappears when the program ends. Files let you:
- Save game progress
- Store user settings
- Keep logs and records
- Process data from other sources

---

## Mini-Lessons in This Module

| Mini | Topic | Focus |
|------|-------|-------|
| [mini-1](mini-1_reading.md) | Reading Files | Opening and reading file content |
| [mini-2](mini-2_writing.md) | Writing Files | Creating and writing to files |
| [mini-3](mini-3_paths.md) | Paths & Errors | File paths, checking existence, error handling |

---

## Key Vocabulary

| Term | Simple Definition | Example |
|------|-------------------|---------|
| **Path** | Location of a file | `"data/scores.txt"` |
| **Read** | Get content from file | Load saved data |
| **Write** | Put content into file | Save new data |
| **Append** | Add to end of file | Add to a log |

---

## Quick Reference

```sona
import io

// Read entire file
let content = io.read("myfile.txt")

// Read as lines
let lines = io.read_lines("myfile.txt")

// Write to file (creates or overwrites)
io.write("output.txt", "Hello, World!")

// Append to file
io.append("log.txt", "New log entry\n")

// Check if file exists
if io.exists("config.txt") {
    print("Config found!")
}
```

---

## Common Mistakes

❌ **Forgetting files might not exist**
```sona
let data = io.read("missing.txt")  // Error if file doesn't exist!
```

✅ **Check first or use try/catch**
```sona
if io.exists("missing.txt") {
    let data = io.read("missing.txt")
} else {
    print("File not found")
}
```

---

## Practice Challenges

### Challenge 1: Save a Message
Write your name to a file called `greeting.txt`, then read it back and print it.

### Challenge 2: Line Counter
Read a file and count how many lines it has.

### Challenge 3: Simple Logger
Create a function that appends timestamped messages to a log file.

---

## Next Steps
→ Continue to [Module 08: Error Handling](../08_errors/README.md)
