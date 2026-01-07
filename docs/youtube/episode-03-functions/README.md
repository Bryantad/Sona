# Episode 03: Functions 🔧

> Create reusable blocks of code

## Episode Overview

**Duration:** 20 minutes  
**Level:** Beginner  
**Goal:** Understand functions, parameters, and return values

---

## Script Outline

### Intro (0:00 - 0:30)
"So far, we've been writing code that runs once. But what if you need to do the same thing many times? Functions let you write code once and use it whenever you need it!"

### What is a Function? (0:30 - 2:30)
"A function is like a recipe:
- Has a name
- Takes ingredients (parameters)
- Produces a result (return value)"

```sona
// Using a built-in function
print("Hello!")  // print is a function!
```

### Creating Functions (2:30 - 5:00)
```sona
func greet() {
    print("Hello!")
    print("Welcome to Sona!")
}

// Call the function
greet()
greet()  // Can call it many times!
```

"Anatomy of a function:
- `func` = keyword to create function
- `greet` = the name
- `()` = where parameters go
- `{}` = the code to run"

### Parameters (5:00 - 8:00)
```sona
func greet(name) {
    print("Hello, " + name + "!")
}

greet("Alice")  // Hello, Alice!
greet("Bob")    // Hello, Bob!
```

"Multiple parameters:"
```sona
func introduce(name, age) {
    print(name + " is " + str(age) + " years old")
}

introduce("Alice", 25)
introduce("Bob", 30)
```

### Return Values (8:00 - 11:00)
```sona
func add(a, b) {
    return a + b
}

let result = add(5, 3)
print(result)  // 8

// Use directly
print(add(10, 20))  // 30
```

"More examples:"
```sona
func double(n) {
    return n * 2
}

func isAdult(age) {
    return age >= 18
}

print(double(5))      // 10
print(isAdult(21))    // true
print(isAdult(15))    // false
```

### Default Parameters (11:00 - 13:00)
```sona
func greet(name, greeting = "Hello") {
    print(greeting + ", " + name + "!")
}

greet("Alice")              // Hello, Alice!
greet("Bob", "Hi")          // Hi, Bob!
greet("Carol", "Welcome")   // Welcome, Carol!
```

### Practical Example: Calculator (13:00 - 17:00)
```sona
func add(a, b) {
    return a + b
}

func subtract(a, b) {
    return a - b
}

func multiply(a, b) {
    return a * b
}

func divide(a, b) {
    if b == 0 {
        return "Cannot divide by zero!"
    }
    return a / b
}

// Using our calculator
print(add(10, 5))       // 15
print(subtract(10, 5))  // 5
print(multiply(10, 5))  // 50
print(divide(10, 5))    // 2
print(divide(10, 0))    // Cannot divide by zero!
```

### Outro (17:00 - 20:00)
- Recap: Functions are reusable code blocks
- Parameters pass data in
- Return sends data out
- Challenge: Create a function that calculates the area of a rectangle
- Next: Control flow with if/else

---

## Mini-Episodes

1. [mini-1: Creating Functions](mini-1_creating.md) - 5 min
2. [mini-2: Parameters & Returns](mini-2_params.md) - 5 min
3. [mini-3: Practical Functions](mini-3_practical.md) - 5 min

---

## Code Examples

```sona
// Temperature converter
func celsiusToFahrenheit(celsius) {
    return (celsius * 9/5) + 32
}

func fahrenheitToCelsius(fahrenheit) {
    return (fahrenheit - 32) * 5/9
}

print(celsiusToFahrenheit(0))    // 32
print(celsiusToFahrenheit(100))  // 212
print(fahrenheitToCelsius(98.6)) // 37
```

---

## Keywords
functions, parameters, return values, code reuse, sona functions
