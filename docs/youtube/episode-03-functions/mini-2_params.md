# Mini-Episode 3.2: Parameters & Returns

> Passing data in and getting results out

## Script

### Intro (0:00 - 0:15)
"Functions become powerful when they can receive and return data!"

### Parameters: Data Going In (0:15 - 1:45)
```sona
func greet(name) {
    print("Hello, " + name + "!")
}

greet("Alice")  // Hello, Alice!
greet("Bob")    // Hello, Bob!
```

"The parameter `name` is like a variable that gets filled in when you call the function."

"Multiple parameters:"
```sona
func introduce(name, age) {
    print(name + " is " + str(age) + " years old")
}

introduce("Alice", 25)  // Alice is 25 years old
```

### Return: Data Coming Out (1:45 - 3:15)
"Sometimes you want a result back:"
```sona
func add(a, b) {
    return a + b
}

let sum = add(5, 3)
print(sum)  // 8

// Or use directly
print(add(10, 20))  // 30
```

"The `return` keyword sends a value back."

### Combining Both (3:15 - 4:15)
```sona
func calculateArea(width, height) {
    let area = width * height
    return area
}

let roomArea = calculateArea(10, 12)
print("Area: " + str(roomArea) + " sq ft")  // Area: 120 sq ft
```

### Default Values (4:15 - 4:45)
```sona
func greet(name, greeting = "Hello") {
    return greeting + ", " + name + "!"
}

print(greet("Alice"))           // Hello, Alice!
print(greet("Bob", "Hi"))       // Hi, Bob!
```

### Outro (4:45 - 5:00)
"Parameters = data in. Return = data out. This makes functions incredibly flexible!"

---

## Visual Notes
- Arrow showing data flowing INTO function (parameters)
- Arrow showing data flowing OUT (return)
- Box diagram: inputs -> function -> output
