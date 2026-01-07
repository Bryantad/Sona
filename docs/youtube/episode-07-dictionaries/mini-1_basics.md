# Mini-Episode 7.1: Dictionary Basics

## Script

### Intro (0:00 - 0:15)
"Dictionaries store data with labels - like a real dictionary where you look up words!"

### Creating (0:15 - 1:30)
```sona
// Key: Value pairs
let person = {
    "name": "Alice",
    "age": 25,
    "email": "alice@example.com"
}

// Keys are strings, values can be anything
let mixed = {
    "count": 42,
    "active": true,
    "tags": ["a", "b", "c"]
}
```

### Accessing (1:30 - 2:30)
```sona
let car = {"brand": "Toyota", "year": 2020}

// Bracket notation
print(car["brand"])  // Toyota

// Dot notation (simpler!)
print(car.brand)     // Toyota
print(car.year)      // 2020
```

### Adding & Updating (2:30 - 3:30)
```sona
let book = {"title": "Sona Guide"}

// Add new key
book["author"] = "You"
book.pages = 200

// Update existing
book.title = "Complete Sona Guide"

print(book)
// {"title": "Complete Sona Guide", "author": "You", "pages": 200}
```

### Removing (3:30 - 4:15)
```sona
let data = {"a": 1, "b": 2, "c": 3}
delete data.b
print(data)  // {"a": 1, "c": 3}
```

### Checking Keys (4:15 - 4:45)
```sona
let user = {"name": "Alice"}

if "name" in user {
    print("Has name!")
}

if "age" not in user {
    print("No age set")
}
```

### Outro (4:45 - 5:00)
"Dictionaries: key-value pairs for organized data. Use dot notation for easy access!"
