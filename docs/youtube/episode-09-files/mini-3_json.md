# Mini-Episode 9.3: JSON Files 🗄️

> The perfect format for structured data

---

## What is JSON?

**JSON** = JavaScript Object Notation

It's a text format that looks like dictionaries and lists:

```json
{
    "name": "Alice",
    "age": 25,
    "hobbies": ["reading", "gaming"]
}
```

**Why JSON?**
- Human readable
- Works everywhere
- Perfect for saving complex data

---

## Reading JSON

```sona
import json

// Read JSON file
let data = json.load("user.json")

// Now it's a dictionary!
print(data["name"])     // Alice
print(data["hobbies"])  // ["reading", "gaming"]
```

---

## Writing JSON

```sona
import json

let user = {
    "name": "Bob",
    "level": 10,
    "inventory": ["sword", "shield", "potion"]
}

// Save to JSON file
json.save("player.json", user)
```

This creates a nicely formatted file!

---

## JSON vs Text Files

**Text file:**
```
name=Alice
age=25
```
You have to parse it yourself 😓

**JSON file:**
```json
{"name": "Alice", "age": 25}
```
Sona does the parsing for you! 😊

---

## Practical: Settings Manager

```sona
import json
import fs

func load_settings() {
    if fs.exists("settings.json") {
        return json.load("settings.json")
    }
    // Return defaults
    return {
        "theme": "light",
        "volume": 80,
        "notifications": true
    }
}

func save_settings(settings) {
    json.save("settings.json", settings)
}

// Usage
let settings = load_settings()
settings["theme"] = "dark"
save_settings(settings)
```

---

## Practical: High Score System

```sona
import json
import fs

func load_scores() {
    if fs.exists("scores.json") {
        return json.load("scores.json")
    }
    return []
}

func add_score(name, score) {
    let scores = load_scores()
    scores.append({"name": name, "score": score})
    
    // Sort by score (highest first)
    scores = sorted(scores, key=lambda x: -x["score"])
    
    // Keep top 10
    scores = scores[:10]
    
    json.save("scores.json", scores)
}

func show_leaderboard() {
    let scores = load_scores()
    print("=== HIGH SCORES ===")
    for i, entry in enumerate(scores) {
        print(f"{i+1}. {entry['name']}: {entry['score']}")
    }
}
```

---

## Convert Strings ↔ JSON

```sona
import json

// Dictionary to JSON string
let data = {"x": 10, "y": 20}
let json_string = json.dumps(data)
print(json_string)  // '{"x": 10, "y": 20}'

// JSON string to dictionary
let text = '{"name": "Test"}'
let obj = json.loads(text)
print(obj["name"])  // Test
```

---

## Quick Reference

| Function | What It Does |
|----------|--------------|
| `json.load(file)` | Read JSON file → dictionary |
| `json.save(file, data)` | Save dictionary → JSON file |
| `json.loads(string)` | Parse JSON string → dictionary |
| `json.dumps(data)` | Convert dictionary → JSON string |

---

## When to Use JSON

✅ **Use JSON for:**
- User settings/preferences
- Game save data
- Configuration files
- Data exchange

❌ **Not great for:**
- Large datasets (use database)
- Binary files (images, audio)
- Logs (just use text)
