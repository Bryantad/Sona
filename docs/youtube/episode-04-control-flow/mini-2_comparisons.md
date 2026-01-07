# Mini-Episode 4.2: Comparisons

> How to compare values

## Script

### Intro (0:00 - 0:15)
"Let's learn all the ways to compare things in Sona!"

### Comparison Operators (0:15 - 2:00)
```sona
let a = 10
let b = 5

// Equal to
print(a == b)   // false
print(a == 10)  // true

// Not equal to
print(a != b)   // true

// Greater than / Less than
print(a > b)    // true
print(a < b)    // false

// Greater/Less than OR equal
print(a >= 10)  // true
print(a <= 5)   // false
```

### Combining with AND (2:00 - 3:00)
"Both must be true:"
```sona
let age = 25
let hasID = true

if age >= 21 and hasID {
    print("Welcome!")
}
```

```sona
// true AND true = true
// true AND false = false
// false AND true = false
// false AND false = false
```

### Combining with OR (3:00 - 4:00)
"At least one must be true:"
```sona
let isStudent = false
let isSenior = true

if isStudent or isSenior {
    print("You get a discount!")
}
```

```sona
// true OR true = true
// true OR false = true
// false OR true = true
// false OR false = false
```

### NOT (4:00 - 4:30)
"Flip true to false (and vice versa):"
```sona
let isLoggedIn = false

if !isLoggedIn {
    print("Please log in")
}
```

### Outro (4:30 - 5:00)
"Comparisons return true or false. Combine them with AND, OR, and NOT for complex conditions!"

---

## Visual Notes
- Truth tables for AND/OR
- Visual comparison operators
- Examples with checkmarks/X marks
