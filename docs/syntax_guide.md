# Sona Language Syntax Guide

This document outlines important syntax patterns and requirements in the Sona programming language.

## Variable Declaration and Reassignment

In Sona, variables are declared using the `let` keyword:

```sona
let name = "Alice"
let age = 30
```

**Variable reassignment works normally without requiring `let`**:

```sona
// Initial declaration
let counter = 0

// Reassignment (no 'let' needed)
counter = counter + 1
counter = 10
name = "Bob"
```

✅ Both declaration and reassignment work correctly:

```sona
let x = 5        // Declaration with 'let'
x = 10           // Reassignment without 'let'
x = x + 5        // Mathematical reassignment
```

## Boolean Values

Sona supports both integer values and boolean literals:

**Boolean literals (v0.5.1+):**

```sona
let is_active = true   // Boolean true
let is_deleted = false // Boolean false
```

**Integer values (traditional):**

```sona
let is_active = 1  // true
let is_deleted = 0 // false
```

Both work correctly in conditional statements:

```sona
if is_active {
    print("Active!")
}
```

## Comparison Operators

Sona supports all standard comparison operators:

```sona
let a = 10
let b = 5

// All comparison operators work
if a > b {
    print("a is greater than b")
}

if a >= b {
    print("a is greater than or equal to b")
}

if a == b {
    print("a equals b")
}

if a != b {
    print("a is not equal to b")
}

if b < a {
    print("b is less than a")
}

if b <= a {
    print("b is less than or equal to a")
}
```

❌ This will cause an error:

```sona
if x < 10 {  // Error: '<' operator not supported
    print("x is less than 10")
}

if x == 10 {  // Error: '==' operator not supported
    print("x equals 10")
}
```

## Return Statements

All functions in Sona must include a return value. Empty returns are not allowed:

```sona
// Correct: Return with value
func greet(name) {
    print("Hello, " + name)
    return 0  // Return 0 as a default value
}
```

❌ This will cause an error:

```sona
func greet(name) {
    print("Hello, " + name)
    return  // Error: Return statement must include a value
}
```

## String Operations

String concatenation uses the `+` operator:

```sona
let full_name = first_name + " " + last_name
```

For other string operations, use the string module:

```sona
import utils.string.smod as string

let length = string.length(name)
let substring = string.substr(name, 0, 3)
let has_prefix = string.startswith(name, "Mr.")
```

## Working with Arrays

Arrays are created using square brackets:

```sona
let numbers = [1, 2, 3, 4]
```

Array operations are performed using the array module:

```sona
import utils.array.smod as array

// Get array length
let length = array.length(numbers)

// Access element
let first = array.get(numbers, 0)

// Add element
array.push(numbers, 5)

// Remove last element
let last = array.pop(numbers)
```

## Module System

Sona modules can be imported using the `import` statement:

```sona
// Direct import
import fs.smod
fs.write_file("example.txt", "Hello, World!")

// Import with alias
import http.smod as http
http.get("https://example.com")
```

### Native Function Calls

Sona supports native function calls through the `__native__` namespace. These functions are implemented in Python and exposed to Sona:

```sona
// Native functions are typically not called directly
// They are used by .smod modules as an implementation detail

// Example of how module functions use native functions internally:
func exists(path) {
    return __native__.fs_exists(path)
}
```

## Standard Library Modules

### File System (fs.smod)

```sona
import fs.smod

// Check if file exists
let exists = fs.exists("file.txt")

// Read file
let content = fs.read_file("file.txt")

// Write file
fs.write_file("output.txt", "Hello, World!")

// Create directory
fs.makedirs("new_folder")

// List directory
let files = fs.listdir(".")
```

### HTTP (http.smod)

```sona
import http.smod

// GET request
let response = http.get("https://example.com")

// POST request with data
let post_data = {"name": "Sona", "version": "0.5.1"}
let response = http.post("https://example.com/api", post_data)
```

## Best Practices

1. Use descriptive names for variables and functions
2. Import necessary modules at the beginning of your file
3. Use boolean literals (`true`/`false`) rather than integers (0/1) when possible
4. Remember that variable reassignment doesn't require the `let` keyword
5. Add comments to explain complex logic
6. Use modules for advanced functionality
7. Prefer using built-in functions over reimplementing common operations
