# Mini-Lesson 5.2: Dictionaries

## What is a Dictionary?

A **dictionary** stores data in **key-value pairs**. Instead of using number positions (like lists), you use **names** (keys) to find values.

Think of it like:
- A real dictionary: word → definition
- A phone book: name → phone number
- A student ID: ID number → student info

---

## Creating Dictionaries

```sona
// Empty dictionary
let empty = {}

// Dictionary with data
let person = {
    "name": "Alex",
    "age": 16,
    "city": "Seattle"
}
```

### Visual Representation

```
person = {
    "name" → "Alex"
    "age"  → 16
    "city" → "Seattle"
}
```

Each **key** (left) points to a **value** (right).

---

## Accessing Values

### Two Ways to Access

```sona
let user = {
    "username": "gamer42",
    "score": 1500
}

// Method 1: Bracket notation
print(user["username"])  // "gamer42"

// Method 2: Dot notation
print(user.username)     // "gamer42"
```

**Use dot notation when the key is a simple word.**  
**Use brackets when the key has spaces or special characters.**

---

## Adding and Changing Values

```sona
let profile = {
    "name": "Jordan"
}

// Add new key-value pair
profile["email"] = "jordan@email.com"
profile.age = 25

// Change existing value
profile["name"] = "Jordan Smith"

print(profile)
// {"name": "Jordan Smith", "email": "jordan@email.com", "age": 25}
```

---

## Removing Keys

```sona
let data = {
    "a": 1,
    "b": 2,
    "c": 3
}

delete data["b"]
print(data)  // {"a": 1, "c": 3}
```

---

## Checking if a Key Exists

```sona
let settings = {
    "volume": 80,
    "brightness": 50
}

if "volume" in settings {
    print("Volume is set to: " + settings.volume)
}

if "theme" not in settings {
    print("Theme not configured yet")
}
```

---

## Getting All Keys or Values

```sona
let inventory = {
    "apples": 10,
    "bananas": 5,
    "oranges": 8
}

let allKeys = inventory.keys()
// ["apples", "bananas", "oranges"]

let allValues = inventory.values()
// [10, 5, 8]
```

---

## Nested Dictionaries

Dictionaries can contain other dictionaries:

```sona
let student = {
    "name": "Taylor",
    "grades": {
        "math": 95,
        "english": 88,
        "science": 92
    }
}

// Access nested value
print(student.grades.math)      // 95
print(student["grades"]["english"])  // 88
```

---

## When to Use Lists vs Dictionaries

| Use a **List** when... | Use a **Dictionary** when... |
|------------------------|------------------------------|
| Order matters | You need named access |
| Items are similar | Items have different meanings |
| You access by position | You access by name/key |
| Example: high scores | Example: player stats |

```sona
// List: ordered collection
let highScores = [1000, 950, 900, 850]

// Dictionary: named properties
let player = {
    "name": "Alex",
    "health": 100,
    "level": 5
}
```

---

## Practice

### Exercise 1
Create a dictionary for a book with keys: `title`, `author`, `pages`. Print the title.

### Exercise 2
Create a dictionary for yourself. Add your favorite food after creating it.

### Exercise 3
What will this print?
```sona
let pet = {
    "type": "dog",
    "name": "Buddy",
    "age": 3
}
print(pet.name)
print(pet["type"])
```

<details>
<summary>Answer</summary>

```
Buddy
dog
```

</details>

---

## Summary

| Operation | Code | Result |
|-----------|------|--------|
| Create | `let d = {"a": 1}` | New dictionary |
| Access | `d["a"]` or `d.a` | Get value |
| Add/Change | `d["b"] = 2` | Set value |
| Delete | `delete d["a"]` | Remove key |
| Check key | `"a" in d` | true/false |
| Get keys | `d.keys()` | List of keys |

---

→ Next: [mini-3: Iterating Collections](mini-3_iteration.md)
