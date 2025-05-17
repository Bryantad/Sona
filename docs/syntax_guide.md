# Sona Language Syntax Guide

This document outlines important syntax patterns and requirements in the Sona programming language.

## Variable Declaration and Reassignment

In Sona, variables are declared using the `let` keyword:

```sona
let name = "Alice"
let age = 30
```

Unlike many other languages, **Sona requires using `let` each time you reassign a variable**:

```sona
// Initial declaration
let counter = 0

// Reassignment (notice 'let' is required again)
let counter = counter + 1
```

❌ This will cause an error:

```sona
counter = counter + 1  // Error: Missing 'let' keyword
```

## Boolean Values

Sona uses integers for boolean values instead of boolean literals:

- `1` for true
- `0` for false

Example:

```sona
let is_active = 1  // true
let is_deleted = 0  // false

if is_active {
    print("Active!")
}
```

❌ This will cause an error:

```sona
let is_active = true  // Error: 'true' is not defined
```

## Comparison Operators

Sona doesn't support standard comparison operators like `<`, `>`, `<=`, `>=`. Instead, you need to use helper functions:(yet)

```sona
// Helper function: check if a < b
func is_less_than(a, b) {
    let diff = math.subtract(a, b)
    return is_negative(diff)
}

// Helper function: check if a > b
func is_greater_than(a, b) {
    return is_less_than(b, a)
}
```

For equality, use `math.eq()`:

```sona
// Check equality
if math.eq(x, 10) {
    print("x equals 10")
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

## Best Practices

1. Always include helper functions for comparisons in your code
2. Use integers (0/1) consistently for boolean logic
3. Always return a value from functions, even if just `return 0`
4. Remember to use `let` for every variable reassignment
5. Import necessary modules at the beginning of your file
6. Use descriptive names for variables and functions
7. Add comments to explain complex logic or workarounds
