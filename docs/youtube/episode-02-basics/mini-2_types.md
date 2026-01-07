# Mini-Episode 2.2: Data Types

> Numbers, text, and true/false values

## Script

### Intro (0:00 - 0:15)
"Data comes in different types. Let's learn the main three!"

### Numbers (0:15 - 1:30)
```sona
// Integers (whole numbers)
let age = 25
let score = 100
let temperature = -5

// Floats (decimal numbers)  
let price = 19.99
let pi = 3.14159
let percentage = 0.75
```

"You can do math with numbers:"
```sona
let a = 10
let b = 3

print(a + b)   // 13 (addition)
print(a - b)   // 7  (subtraction)
print(a * b)   // 30 (multiplication)
print(a / b)   // 3.333... (division)
print(a % b)   // 1  (remainder)
```

### Strings (Text) (1:30 - 2:45)
```sona
let name = "Alex"
let message = "Hello, World!"
let emoji = "🚀"
```

"Combine strings with `+`:"
```sona
let first = "Hello"
let second = "World"
let combined = first + ", " + second + "!"
print(combined)  // Hello, World!
```

### Booleans (True/False) (2:45 - 3:45)
```sona
let isStudent = true
let hasLicense = false
let isAdult = age >= 18
```

"Booleans answer yes/no questions:
- Is the user logged in? `true`
- Is the game over? `false`"

### Type Conversion (3:45 - 4:30)
```sona
// Number to string
let age = 25
print("I am " + str(age) + " years old")

// String to number
let input = "42"
let number = int(input)
print(number + 8)  // 50
```

### Outro (4:30 - 5:00)
"Three types: numbers for math, strings for text, booleans for yes/no. Sona figures out types automatically!"

---

## Visual Notes
- Color code: Numbers=blue, Strings=green, Booleans=orange
- Show type icons next to examples
- Animate math operations
