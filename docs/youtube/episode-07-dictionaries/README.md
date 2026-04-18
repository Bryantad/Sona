# Episode 07: Dictionaries 📖

> Key-value data storage

## Episode Overview

**Duration:** 15 minutes  
**Level:** Beginner  
**Goal:** Create and use dictionaries for structured data

---

## Script Outline

### Intro (0:00 - 0:30)
"Lists are great, but what if you want to look up data by name instead of position? Dictionaries!"

### Creating Dictionaries (0:30 - 3:00)
```sona
let person = {
    "name": "Alice",
    "age": 25,
    "city": "New York"
}

let empty = {}
```

### Accessing Values (3:00 - 6:00)
```sona
let person = {"name": "Alice", "age": 25}
print(person["name"])   // Alice
print(person.name)      // Alice (shorthand)
print(person.age)       // 25
```

### Modifying Dictionaries (6:00 - 9:00)
```sona
let person = {"name": "Alice"}
person["age"] = 25          // Add new key
person.city = "Boston"      // Add with dot notation
person["name"] = "Alicia"   // Update existing
delete person.city          // Remove key
```

### Checking Keys (9:00 - 11:00)
```sona
let data = {"x": 10, "y": 20}
print("x" in data)    // true
print("z" in data)    // false
```

### Looping (11:00 - 13:00)
```sona
let scores = {"Alice": 95, "Bob": 87, "Carol": 92}

for name, score in scores.items() {
    print(name + ": " + str(score))
}
```

### Nested Dictionaries (13:00 - 14:30)
```sona
let user = {
    "name": "Alice",
    "address": {
        "city": "Boston",
        "zip": "02101"
    }
}
print(user.address.city)  // Boston
```

### Outro (14:30 - 15:00)
- Challenge: Create a contact book
- Next: Strings in depth

---

## Mini-Episodes
1. [mini-1: Dictionary Basics](mini-1_basics.md)
2. [mini-2: Dictionary Methods](mini-2_methods.md)
3. [mini-3: Nested Data](mini-3_nested.md)
