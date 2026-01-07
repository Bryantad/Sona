# Mini-Episode 10.1: Try/Catch Basics ⚠️

> Handle errors gracefully

---

## What Are Errors?

**Errors** happen when something goes wrong:
- File doesn't exist
- Dividing by zero
- Wrong type of data
- Network connection fails

Without handling: Your program crashes! 💥

With handling: You deal with it gracefully 😎

---

## The Try/Catch Pattern

```sona
try {
    // Code that might fail
    let result = 10 / 0  // This will fail!
} catch error {
    // What to do if it fails
    print(f"Oops! Something went wrong: {error}")
}

print("Program continues...")  // Still runs!
```

---

## How It Works

```
try {
    ↓ Run this code
    ↓ If error happens → JUMP to catch
    ↓ If no error → skip catch
}
catch {
    ← Handle the error here
}
↓ Program continues either way
```

---

## Real Example: File Reading

```sona
func load_data(filename) {
    try {
        let content = read_file(filename)
        return content
    } catch error {
        print(f"Could not read {filename}")
        return ""  // Return empty string instead
    }
}

// Safe to use!
let data = load_data("maybe_exists.txt")
```

---

## The Finally Block

Code that **always** runs, error or not:

```sona
try {
    // Try something risky
    let data = risky_operation()
} catch error {
    print("It failed!")
} finally {
    // This ALWAYS runs
    print("Cleaning up...")
}
```

**Use finally for:**
- Closing files
- Cleaning up resources
- Logging that something completed

---

## Try/Catch with User Input

```sona
func get_number() {
    while true {
        let input = prompt("Enter a number: ")
        
        try {
            let num = int(input)  // Might fail!
            return num
        } catch error {
            print("That's not a valid number. Try again!")
        }
    }
}

let age = get_number()  // Keeps asking until valid
```

---

## Pattern: Safe Division

```sona
func safe_divide(a, b) {
    try {
        return a / b
    } catch error {
        print("Cannot divide by zero!")
        return 0
    }
}

print(safe_divide(10, 2))  // 5
print(safe_divide(10, 0))  // Cannot divide... 0
```

---

## Key Points

1. **try** = "Attempt this code"
2. **catch** = "If it fails, do this"
3. **finally** = "Always do this at the end"
4. Program **continues** after catch
5. Without try/catch, errors **crash** your program
