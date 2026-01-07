# Mini-Lesson 7.3: Paths & Error Handling

## What is a File Path?

A **path** tells the computer where to find a file. It's like an address.

---

## Types of Paths

### Relative Paths (Recommended)
Relative to where your program runs:

```sona
"data.txt"              // Same folder as program
"data/scores.txt"       // In 'data' subfolder
"../config.txt"         // Parent folder (one level up)
```

### Absolute Paths
Full path from the root:

```sona
// Windows
"C:/Users/Alex/Documents/data.txt"

// Mac/Linux
"/home/alex/documents/data.txt"
```

**Tip:** Use forward slashes `/` even on Windows—Sona handles it.

---

## Working with Paths

```sona
import path

// Join path parts safely
let filePath = path.join("data", "users", "scores.txt")
// Result: "data/users/scores.txt"

// Get just the filename
let name = path.basename("data/users/scores.txt")
// Result: "scores.txt"

// Get the directory
let dir = path.dirname("data/users/scores.txt")
// Result: "data/users"

// Get file extension
let ext = path.extension("photo.jpg")
// Result: ".jpg"
```

---

## Checking Files and Folders

### Does It Exist?

```sona
import io

if io.exists("config.txt") {
    print("Config file found!")
} else {
    print("No config file - using defaults")
}
```

### Is It a File or Folder?

```sona
import io

if io.is_file("data.txt") {
    print("It's a file")
}

if io.is_directory("data") {
    print("It's a folder")
}
```

---

## Creating Directories

```sona
import io

// Create a folder
io.create_directory("output")

// Create nested folders
io.create_directory("data/users/logs")  // Creates all needed folders
```

---

## Listing Directory Contents

```sona
import io

let files = io.list_directory("data")

for file in files {
    print(file)
}
```

---

## Error Handling with Files

Files can cause errors:
- File doesn't exist
- No permission to read/write
- Disk is full
- File is locked by another program

### Using try/catch

```sona
import io

try {
    let content = io.read("maybe_missing.txt")
    print(content)
} catch e {
    print("Could not read file: " + e.message)
}
```

### Check First, Then Act

```sona
import io

let filename = "data.txt"

if io.exists(filename) {
    let content = io.read(filename)
    print(content)
} else {
    print("File not found: " + filename)
}
```

---

## Safe File Operations Pattern

```sona
import io

func safeRead(filename, defaultValue = "") {
    if io.exists(filename) {
        try {
            return io.read(filename)
        } catch e {
            print("Error reading {filename}: {e.message}")
            return defaultValue
        }
    }
    return defaultValue
}

// Usage
let content = safeRead("config.txt", "default settings")
```

---

## Deleting Files

**Warning:** Deleted files are gone forever!

```sona
import io

// Delete a file
if io.exists("temp.txt") {
    io.delete("temp.txt")
    print("File deleted")
}

// Delete a folder (must be empty)
io.delete_directory("old_data")
```

---

## Copying and Moving Files

```sona
import io

// Copy file
io.copy("original.txt", "backup.txt")

// Move/rename file
io.move("old_name.txt", "new_name.txt")
```

---

## Practical Example: Config File Manager

```sona
import io

let CONFIG_FILE = "settings.conf"

func loadConfig() {
    if not io.exists(CONFIG_FILE) {
        // Create default config
        let defaults = {
            "theme": "light",
            "volume": 50,
            "language": "en"
        }
        saveConfig(defaults)
        return defaults
    }
    
    try {
        let lines = io.read_lines(CONFIG_FILE)
        let config = {}
        
        for line in lines {
            if line.contains("=") {
                let parts = line.split("=")
                config[parts[0].trim()] = parts[1].trim()
            }
        }
        
        return config
    } catch e {
        print("Error loading config: {e.message}")
        return {}
    }
}

func saveConfig(config) {
    let content = ""
    for key, value in config.items() {
        content = content + "{key}={value}\n"
    }
    
    try {
        io.write(CONFIG_FILE, content)
        print("Config saved!")
    } catch e {
        print("Error saving config: {e.message}")
    }
}

// Usage
let settings = loadConfig()
print("Theme: " + settings.theme)

settings.theme = "dark"
saveConfig(settings)
```

---

## Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| File not found | Path is wrong or file deleted | Check path, use `exists()` |
| Permission denied | No rights to access | Check file permissions |
| Directory not empty | Trying to delete non-empty folder | Delete contents first |
| Invalid path | Bad characters in filename | Avoid special characters |

---

## Practice

### Exercise 1
Write code that checks if "data" folder exists. If not, create it.

### Exercise 2
List all files in the current directory and print each one.

### Exercise 3
Create a function that safely reads a file, returning an empty string if anything goes wrong.

<details>
<summary>Exercise 3 Answer</summary>

```sona
import io

func safeRead(filename) {
    try {
        if io.exists(filename) {
            return io.read(filename)
        }
    } catch e {
        // Silently handle error
    }
    return ""
}

let content = safeRead("maybe.txt")
```

</details>

---

## Summary

| Operation | Code |
|-----------|------|
| Check exists | `io.exists("file.txt")` |
| Is file | `io.is_file("file.txt")` |
| Is directory | `io.is_directory("folder")` |
| Create directory | `io.create_directory("folder")` |
| List directory | `io.list_directory("folder")` |
| Delete file | `io.delete("file.txt")` |
| Copy file | `io.copy("src", "dest")` |
| Move file | `io.move("old", "new")` |
| Join paths | `path.join("a", "b", "c")` |

---

## Module 07 Complete! 🎉

You've learned:
- ✅ Reading files
- ✅ Writing and appending to files
- ✅ Working with paths
- ✅ Handling file errors safely

→ Next: [Module 08: Error Handling](../08_errors/README.md)
