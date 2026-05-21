# Mini-Episode 9.1: Reading Files 📖

> Get data from text files into your program

---

## Why Read Files?

- Load saved data
- Process text documents
- Read configuration
- Import user content

---

## Basic File Reading

```sona
// Read entire file at once
let content = read_file("story.txt")
print(content)
```

**Simple as that!**

---

## Read Lines as a List

```sona
// Each line becomes a list item
let lines = read_lines("names.txt")

for line in lines {
    print(f"Name: {line}")
}
```

If `names.txt` contains:
```
Alice
Bob
Charlie
```

Output:
```
Name: Alice
Name: Bob
Name: Charlie
```

---

## Check If File Exists

```sona
import fs

if fs.exists("myfile.txt") {
    let content = read_file("myfile.txt")
    print(content)
} else {
    print("File not found!")
}
```

**Always check first** to avoid errors!

---

## Handle Errors Gracefully

```sona
try {
    let content = read_file("maybe_exists.txt")
    print(content)
} catch error {
    print(f"Could not read file: {error}")
}
```

---

## Practical Example: Config Loader

```sona
func load_settings() {
    if not fs.exists("settings.txt") {
        return {"theme": "light", "font_size": 14}  // Defaults
    }
    
    let settings = {}
    let lines = read_lines("settings.txt")
    
    for line in lines {
        let parts = line.split("=")
        if len(parts) == 2 {
            let key = parts[0].strip()
            let value = parts[1].strip()
            settings[key] = value
        }
    }
    
    return settings
}
```

For a file like:
```
theme = dark
font_size = 16
```

---

## Key Points

| Function | What It Does |
|----------|--------------|
| `read_file(path)` | Returns entire file as one string |
| `read_lines(path)` | Returns list of lines |
| `fs.exists(path)` | Returns true/false |

---

## Tips for Reading

1. **Small files**: Use `read_file()` - easy!
2. **Line by line**: Use `read_lines()` - process each
3. **Always handle errors**: Files might not exist
4. **Close files**: Sona does this automatically
