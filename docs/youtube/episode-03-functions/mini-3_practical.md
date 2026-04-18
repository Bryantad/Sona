# Mini-Episode 3.3: Practical Functions

> Real-world function examples

## Script

### Intro (0:00 - 0:15)
"Let's see functions used in real situations!"

### Example 1: Formatting (0:15 - 1:15)
```sona
func formatPrice(amount) {
    return "$" + str(amount)
}

func formatName(first, last) {
    return first + " " + last
}

print(formatPrice(19.99))           // $19.99
print(formatName("John", "Doe"))    // John Doe
```

### Example 2: Calculations (1:15 - 2:15)
```sona
func calculateTip(bill, tipPercent = 18) {
    let tip = bill * (tipPercent / 100)
    return tip
}

let myBill = 50
let tip = calculateTip(myBill)
print("Tip: " + formatPrice(tip))  // Tip: $9.0

// Custom tip percentage
print(formatPrice(calculateTip(100, 20)))  // $20
```

### Example 3: Validation (2:15 - 3:15)
```sona
func isValidEmail(email) {
    return "@" in email and "." in email
}

func isValidAge(age) {
    return age >= 0 and age <= 150
}

print(isValidEmail("test@example.com"))  // true
print(isValidEmail("invalid"))           // false
print(isValidAge(25))                    // true
print(isValidAge(-5))                    // false
```

### Example 4: Building Blocks (3:15 - 4:30)
"Functions can call other functions:"
```sona
func square(n) {
    return n * n
}

func sumOfSquares(a, b) {
    return square(a) + square(b)
}

print(square(4))          // 16
print(sumOfSquares(3, 4)) // 25 (9 + 16)
```

### Outro (4:30 - 5:00)
"Functions help you organize code into small, reusable pieces. Start small, combine them, build amazing things!"

---

## Visual Notes
- Show functions as building blocks
- Diagram of functions calling each other
- Real-world analogies (calculator, validator)
