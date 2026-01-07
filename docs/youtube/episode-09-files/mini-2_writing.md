# Mini-Episode 9.2: Writing Files 📝

> Save data from your program to files

---

## Why Write Files?

- Save user data
- Create logs
- Export results
- Generate reports

---

## Basic File Writing

```sona
// Write text to a file (creates or overwrites)
write_file("output.txt", "Hello, World!")
```

**That's it!** The file is created if it doesn't exist.

---

## Write Multiple Lines

```sona
let lines = [
    "Line 1",
    "Line 2", 
    "Line 3"
]

// Join with newlines
let content = "\n".join(lines)
write_file("myfile.txt", content)
```

Result in file:
```
Line 1
Line 2
Line 3
```

---

## Append to File

```sona
// Add to end of file (don't overwrite)
append_file("log.txt", "New entry\n")

// Useful for logs
func log_event(message) {
    import time
    let timestamp = time.now()
    append_file("app.log", f"[{timestamp}] {message}\n")
}

log_event("User logged in")
log_event("File saved")
```

---

## Write vs Append

| Function | What It Does |
|----------|--------------|
| `write_file()` | **Replaces** entire file |
| `append_file()` | **Adds** to end of file |

⚠️ **Be careful!** `write_file()` erases existing content!

---

## Practical Example: Save Game

```sona
func save_game(player) {
    let save_data = f"""
player_name={player['name']}
level={player['level']}
score={player['score']}
health={player['health']}
"""
    write_file("savegame.txt", save_data)
    print("Game saved!")
}

// Save current game
let player = {
    "name": "Hero",
    "level": 5,
    "score": 1500,
    "health": 100
}
save_game(player)
```

---

## Create Directory First

```sona
import fs

// Make sure folder exists before writing
if not fs.exists("data") {
    fs.mkdir("data")
}

write_file("data/output.txt", "Hello!")
```

---

## Error Handling for Writing

```sona
try {
    write_file("important.txt", data)
    print("File saved successfully!")
} catch error {
    print(f"Failed to save: {error}")
}
```

---

## Pattern: Backup Before Overwrite

```sona
func safe_save(filename, content) {
    import fs
    
    // Create backup if file exists
    if fs.exists(filename) {
        let backup = filename + ".backup"
        let old_content = read_file(filename)
        write_file(backup, old_content)
    }
    
    // Write new content
    write_file(filename, content)
}
```

---

## Quick Tips

1. **New file?** → `write_file()`
2. **Add to existing?** → `append_file()`
3. **Important data?** → Make backups!
4. **Always handle errors** when writing
