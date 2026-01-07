# Episode 04: Control Flow - If/Else 🚦

> Making decisions in your code

## Episode Overview

**Duration:** 15 minutes  
**Level:** Beginner  
**Goal:** Use if/else statements and match expressions

---

## Script Outline

### Intro (0:00 - 0:30)
"Programs need to make decisions. Should I do this OR that? That's what control flow is all about!"

### If Statements (0:30 - 3:00)
```sona
let age = 18

if age >= 18 {
    print("You can vote!")
}
```

"The code inside `{ }` only runs if the condition is `true`."

### If/Else (3:00 - 5:30)
```sona
let age = 15

if age >= 18 {
    print("You can vote!")
} else {
    print("Too young to vote")
}
```

### Else If (5:30 - 8:00)
```sona
let score = 85

if score >= 90 {
    print("A - Excellent!")
} else if score >= 80 {
    print("B - Good!")
} else if score >= 70 {
    print("C - Okay")
} else {
    print("Need improvement")
}
```

### Comparison Operators (8:00 - 10:00)
```sona
// Equal:           ==
// Not equal:       !=
// Greater:         >
// Less:            <
// Greater/equal:   >=
// Less/equal:      <=
```

### Combining Conditions (10:00 - 12:00)
```sona
let age = 25
let hasLicense = true

if age >= 16 and hasLicense {
    print("You can drive!")
}

if age < 13 or age > 65 {
    print("Discount available!")
}
```

### Match Expression (12:00 - 14:00)
```sona
let day = "Monday"

match day {
    "Saturday" | "Sunday" => print("Weekend! 🎉")
    "Friday" => print("Almost weekend!")
    _ => print("Weekday...")
}
```

### Outro (14:00 - 15:00)
- Challenge: Create a simple number guessing game
- Next: Loops - doing things repeatedly

---

## Mini-Episodes

1. [mini-1: If and Else](mini-1_if_else.md) - 5 min
2. [mini-2: Comparisons](mini-2_comparisons.md) - 5 min  
3. [mini-3: Match Expression](mini-3_match.md) - 5 min

---

## Keywords
if else, control flow, conditions, match statement, comparisons
