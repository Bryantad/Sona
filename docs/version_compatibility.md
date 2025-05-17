# Sona Version Compatibility Guide

## Version Features: v0.5.0

This document outlines the key features and syntax for Sona v0.5.0.

### New in v0.5.0

- **Import aliases** with the `as` keyword
- **Improved function parameters** with reliable scope handling
- **Enhanced error messages** with line and column information
- **Multi-line string literals** using triple quotes (`"""` or `'''`)
- **Improved comment handling** including inline comments

### Import Syntax

Sona v0.5.0 supports both direct imports and imports with aliases:

**Direct imports:**

```sona
import utils.math.smod
// Usage:
math.add(1, 2)
```

**Imports with aliases:**

```sona
import utils.math.smod as math
// Usage:
math.add(1, 2)
```

**Note:** When using direct imports, modules are registered with their base name (e.g., "math" for utils.math.smod). Using the `as` keyword allows you to specify a custom name for the imported module.

### Function Parameters

Function parameters work reliably in v0.5.0:

```sona
// Function with parameters
func add_and_print(x, y) {
    let result = math.add(x, y)
    print("Result: " + math.to_str(result))
    return result
}

// Function call
add_and_print(3, 4)  // Output: Result: 7
```

### String Concatenation

Sona requires explicit type conversion when concatenating strings with other types:

```sona
let x = 5
// Error:
print("Value: " + x)  // can only concatenate str (not "float") to str

// Working:
print("Value: " + math.to_str(x))
```

### If-Else Structure

Sona v0.5.0 supports properly nested if-else statements:

```sona
// Proper nesting of if-else blocks:
if condition {
    // code
} else {
    if another_condition {
        // code
    } else {
        // code
    }
}
```

### Variable Reassignment

Variable reassignment requires the `let` keyword:

```sona
let x = 5
// Later...
let x = 10  // Must use 'let' again
```

### Multi-line Strings

Sona v0.5.0 supports multi-line string literals using triple quotes:

```sona
let multiline_text = """
This is a multi-line string.
It can span multiple lines
without needing to use concatenation.
"""

// Triple single quotes also work
let another_multiline = '''
Another multi-line string
using single quotes.
'''
```

## Best Practices for v0.5.0

1. **Use meaningful aliases with imports**:

   ```sona
   import utils.math.smod as math
   // Then use as: math.function()
   ```

2. **Always convert numbers to strings** when concatenating:

   ```sona
   print("Value: " + math.to_str(someNumber))
   ```

3. **Properly nest if-else statements**:

   ```sona
   if condition1 {
       // code
   } else {
       if condition2 {
           // code
       } else {
           // code
       }
   }
   ```

4. **Use let for all variable assignments** including reassignments.

5. **Use multi-line strings** for complex text blocks and template strings.

## Working Examples for v0.5.0

### 1. Basic Math Operations

```sona
import utils.math.smod as math

print("PI value: " + math.to_str(math.PI))
print("2 + 3 = " + math.to_str(math.add(2, 3)))
```

### 2. Simple If-Else

```sona
import utils.math.smod as math

let x = 5
let y = 10

if math.eq(x, y) {
    print("x equals y")
} else {
    print("x is not equal to y")
}
```

### 3. Functions with Parameters

```sona
import utils.math.smod as math

func calculate_area(width, height) {
    let area = math.multiply(width, height)
    return area
}

let area = calculate_area(5, 10)
print("Area: " + math.to_str(area))
```

Updated: May 17, 2025
