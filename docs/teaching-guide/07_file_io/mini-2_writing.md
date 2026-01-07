# Mini-Lesson 7.2: Writing Files

## Why Write Files?

Writing files lets your program:
- Save data permanently
- Create logs and records
- Export results
- Generate reports

---

## Writing to a File

### Basic Write (Creates or Overwrites)

```sona
import io

io.write("output.txt", "Hello, World!")
```

This creates `output.txt` with the content "Hello, World!". If the file already exists, it's completely replaced.

---

## Writing Multiple Lines

### Using Newline Characters

```sona
import io

let content = "Line 1\nLine 2\nLine 3"
io.write("multiline.txt", content)
```

**Result in file:**
```
Line 1
Line 2
Line 3
```

### Using write_lines()

```sona
import io

let lines = ["First line", "Second line", "Third line"]
io.write_lines("output.txt", lines)
```

---

## Appending to Files

Add to the end without erasing existing content:

```sona
import io

// First write
io.write("log.txt", "Program started\n")

// Later, append more
io.append("log.txt", "User logged in\n")
io.append("log.txt", "Action performed\n")
```

**Result in log.txt:**
```
Program started
User logged in
Action performed
```

---

## Building Content Then Writing

Often you build up content, then write once:

```sona
import io

let report = ""
report = report + "=== Daily Report ===\n"
report = report + "Date: 2024-01-15\n"
report = report + "\n"
report = report + "Items processed: 150\n"
report = report + "Errors: 2\n"

io.write("report.txt", report)
```

---

## Writing Data Structures

### Lists to File

```sona
import io

let scores = [100, 95, 87, 92, 78]
let content = ""

for score in scores {
    content = content + score + "\n"
}

io.write("scores.txt", content)
```

### Dictionaries to File

```sona
import io

let settings = {
    "volume": 80,
    "brightness": 50,
    "theme": "dark"
}

let content = ""
for key, value in settings.items() {
    content = content + "{key}={value}\n"
}

io.write("settings.conf", content)
```

**Result:**
```
volume=80
brightness=50
theme=dark
```

---

## Creating a Simple Logger

```sona
import io
import time

func log(message) {
    let timestamp = time.now().format("%Y-%m-%d %H:%M:%S")
    let entry = "[{timestamp}] {message}\n"
    io.append("app.log", entry)
}

// Usage
log("Application started")
log("User clicked button")
log("Data saved successfully")
```

**Result in app.log:**
```
[2024-01-15 10:30:45] Application started
[2024-01-15 10:30:46] User clicked button
[2024-01-15 10:30:47] Data saved successfully
```

---

## Writing CSV Files

```sona
import io

let students = [
    {"name": "Alice", "grade": 95},
    {"name": "Bob", "grade": 87},
    {"name": "Carol", "grade": 92}
]

let csv = "name,grade\n"  // Header row

for student in students {
    csv = csv + "{student.name},{student.grade}\n"
}

io.write("students.csv", csv)
```

**Result:**
```
name,grade
Alice,95
Bob,87
Carol,92
```

---

## Overwrite vs Append

| Function | Behavior |
|----------|----------|
| `io.write()` | Creates new file or **erases** existing |
| `io.append()` | Creates new file or **adds to end** of existing |

**Warning:** `io.write()` destroys existing content!

```sona
// Dangerous if you wanted to keep old data
io.write("important.txt", "new stuff")  // Old data GONE!

// Safe - adds to existing
io.append("important.txt", "new stuff")  // Old data preserved
```

---

## Practical Example: Save Game

```sona
import io

func saveGame(playerName, level, score, inventory) {
    let saveData = ""
    saveData = saveData + "player={playerName}\n"
    saveData = saveData + "level={level}\n"
    saveData = saveData + "score={score}\n"
    saveData = saveData + "inventory={inventory.join(',')}\n"
    
    io.write("savegame.dat", saveData)
    print("Game saved!")
}

func loadGame() {
    let lines = io.read_lines("savegame.dat")
    let data = {}
    
    for line in lines {
        let parts = line.split("=")
        data[parts[0]] = parts[1]
    }
    
    return data
}

// Save
saveGame("Hero", 5, 1500, ["sword", "shield", "potion"])

// Load
let saved = loadGame()
print("Welcome back, {saved.player}!")
```

---

## Practice

### Exercise 1
Write your name and age to a file called `me.txt`.

### Exercise 2
Create a list of 5 favorite foods and save them to `foods.txt`, one per line.

### Exercise 3
Create a logging function that adds timestamped entries to a file.

<details>
<summary>Exercise 2 Answer</summary>

```sona
import io

let foods = ["Pizza", "Tacos", "Sushi", "Pasta", "Burgers"]
let content = ""

for food in foods {
    content = content + food + "\n"
}

io.write("foods.txt", content)
```

</details>

---

## Summary

| Operation | Code | Behavior |
|-----------|------|----------|
| Write | `io.write("f.txt", "text")` | Create/overwrite |
| Append | `io.append("f.txt", "text")` | Add to end |
| Write lines | `io.write_lines("f.txt", list)` | List to file |
| Newline | `"\n"` | Line break |

---

→ Next: [mini-3: Paths & Errors](mini-3_paths.md)
