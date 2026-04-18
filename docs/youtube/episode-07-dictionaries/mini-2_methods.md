# Mini-Episode 7.2: Dictionary Methods

## Script

### Intro (0:00 - 0:15)
"Let's explore the methods that make dictionaries powerful!"

### Getting Keys & Values (0:15 - 1:15)
```sona
let scores = {"Alice": 95, "Bob": 87, "Carol": 92}

print(scores.keys())    // ["Alice", "Bob", "Carol"]
print(scores.values())  // [95, 87, 92]
print(scores.items())   // [["Alice", 95], ["Bob", 87], ...]
```

### Looping (1:15 - 2:15)
```sona
let prices = {"apple": 1.50, "banana": 0.75, "orange": 2.00}

// Loop through keys
for fruit in prices.keys() {
    print(fruit)
}

// Loop through key-value pairs
for fruit, price in prices.items() {
    print("{fruit}: ${price}")
}
```

### Safe Access with get() (2:15 - 3:15)
```sona
let user = {"name": "Alice"}

// This crashes if key doesn't exist!
// print(user["age"])  // Error!

// Safe way with default
print(user.get("age", 0))       // 0
print(user.get("name", "Unknown"))  // Alice
```

### Merging Dictionaries (3:15 - 4:00)
```sona
let defaults = {"theme": "light", "lang": "en"}
let userPrefs = {"theme": "dark"}

let settings = {...defaults, ...userPrefs}
print(settings)
// {"theme": "dark", "lang": "en"}
```

### Length & Clear (4:00 - 4:45)
```sona
let data = {"a": 1, "b": 2, "c": 3}

print(data.length())  // 3

data.clear()
print(data)  // {}
```

### Outro (4:45 - 5:00)
"keys(), values(), items(), get() - these methods handle most dictionary operations!"
