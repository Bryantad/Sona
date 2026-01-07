# Mini-Episode 3.1: Creating Functions

> Write your first custom function

## Script

### Intro (0:00 - 0:15)
"Let's learn how to create our own functions - reusable blocks of code!"

### Why Functions? (0:15 - 1:00)
"Without functions, you repeat yourself:"
```sona
print("===========")
print("  WELCOME  ")
print("===========")

// Later...

print("===========")
print("  WELCOME  ")
print("===========")
```

"With a function, write once, use many times!"

### Creating a Function (1:00 - 2:30)
```sona
func showWelcome() {
    print("===========")
    print("  WELCOME  ")
    print("===========")
}

// Now just call it!
showWelcome()
showWelcome()
```

"The parts:
- `func` - keyword to start
- `showWelcome` - the name (you choose!)
- `()` - empty for now
- `{ }` - the code inside"

### Function Names (2:30 - 3:30)
"Good names describe what the function DOES:"
```sona
// Good names
func calculateTotal() { }
func sendEmail() { }
func isValidPassword() { }

// Bad names
func x() { }
func doStuff() { }
func function1() { }
```

### Calling Functions (3:30 - 4:30)
"Call a function by using its name with `()`:"
```sona
func sayHello() {
    print("Hello!")
}

// Calling it
sayHello()   // Hello!
sayHello()   // Hello!
sayHello()   // Hello!

// This does nothing - just the name
sayHello     // No parentheses = no call!
```

### Outro (4:30 - 5:00)
"Functions group code together. Give them clear names that say what they do. Next: passing data into functions!"

---

## Visual Notes
- Show code being "packaged" into a function
- Arrow showing function call -> function code
- Highlight () as the "trigger"
