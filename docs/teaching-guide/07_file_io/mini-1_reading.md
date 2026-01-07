# Mini-Lesson 7.1: Reading Files

## Why Read Files?

Reading files lets your program access:
- Saved data from previous runs
- Configuration settings
- Data files (CSV, JSON, text)
- Content created by other programs or people

---

## Setting Up

First, import the io module:

```sona
import io
```

---

## Reading an Entire File

The simplest way—get all content as one string:

```sona
import io

let content = io.read("myfile.txt")
print(content)
```

**Example file (`myfile.txt`):**
```
Hello, World!
This is line 2.
And this is line 3.
```

**Output:**
```
Hello, World!
This is line 2.
And this is line 3.
```

---

## Reading Line by Line

Get a list where each item is one line:

```sona
import io

let lines = io.read_lines("myfile.txt")

for line in lines {
    print("Line: " + line)
}
```

**Output:**
```
Line: Hello, World!
Line: This is line 2.
Line: And this is line 3.
```

### Process Each Line

```sona
let lines = io.read_lines("scores.txt")

let total = 0
for line in lines {
    let score = int(line)
    total = total + score
}

print("Total score: " + total)
```

---

## Reading Specific Parts

### First N Lines

```sona
let lines = io.read_lines("bigfile.txt")
let firstFive = lines[0:5]

for line in firstFive {
    print(line)
}
```

### Last Line

```sona
let lines = io.read_lines("log.txt")
let lastLine = lines[-1]
print("Most recent: " + lastLine)
```

---

## Working with File Content

### Count Lines

```sona
let lines = io.read_lines("document.txt")
print("Line count: " + lines.length())
```

### Find a Line

```sona
let lines = io.read_lines("data.txt")

for i, line in enumerate(lines) {
    if line.contains("ERROR") {
        print("Error found on line {i + 1}")
    }
}
```

### Search File Content

```sona
let content = io.read("book.txt")

if content.contains("Chapter 5") {
    print("Chapter 5 exists!")
}
```

---

## File Encodings

Most files use UTF-8 (supports all languages). Specify if needed:

```sona
let content = io.read("japanese.txt", encoding: "utf-8")
```

---

## Common File Types

### Text Files (.txt)
```sona
let notes = io.read("notes.txt")
```

### CSV Files (Comma-Separated)
```sona
let lines = io.read_lines("data.csv")

for line in lines {
    let fields = line.split(",")
    print("Name: {fields[0]}, Age: {fields[1]}")
}
```

### Configuration Files
```sona
let config_lines = io.read_lines("settings.conf")
let settings = {}

for line in config_lines {
    if line.contains("=") {
        let parts = line.split("=")
        settings[parts[0].trim()] = parts[1].trim()
    }
}

print(settings["username"])
```

---

## Practical Example: High Scores

**scores.txt:**
```
Alice,1500
Bob,1200
Carol,1800
Dave,950
```

**Reading and processing:**
```sona
import io

let lines = io.read_lines("scores.txt")
let scores = []

for line in lines {
    let parts = line.split(",")
    scores.push({
        "name": parts[0],
        "score": int(parts[1])
    })
}

// Find highest score
let highest = scores[0]
for entry in scores {
    if entry.score > highest.score {
        highest = entry
    }
}

print("Champion: {highest.name} with {highest.score} points!")
```

---

## Practice

### Exercise 1
Create a text file manually with 3 lines. Write code to read and print each line.

### Exercise 2
Read a file and count how many times the word "the" appears.

### Exercise 3
Create a file with numbers (one per line). Read them and calculate the average.

<details>
<summary>Exercise 3 Answer</summary>

```sona
import io

let lines = io.read_lines("numbers.txt")
let sum = 0

for line in lines {
    sum = sum + int(line)
}

let average = sum / lines.length()
print("Average: " + average)
```

</details>

---

## Summary

| Operation | Code | Result |
|-----------|------|--------|
| Read all | `io.read("file.txt")` | Entire content as string |
| Read lines | `io.read_lines("file.txt")` | List of lines |
| First line | `lines[0]` | First line |
| Last line | `lines[-1]` | Last line |
| Line count | `lines.length()` | Number of lines |

---

→ Next: [mini-2: Writing Files](mini-2_writing.md)
