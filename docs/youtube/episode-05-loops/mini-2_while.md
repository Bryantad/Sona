# Mini-Episode 5.2: While Loops

> Repeat until a condition is false

## Script

### Intro (0:00 - 0:15)
"While loops keep going as long as a condition is true!"

### Basic While (0:15 - 1:30)
```sona
let count = 0

while count < 5 {
    print(count)
    count = count + 1
}
// Output: 0, 1, 2, 3, 4
```

"It checks the condition BEFORE each loop."

### User Input Loop (1:30 - 2:30)
```sona
let password = ""

while password != "secret" {
    password = input("Enter password: ")
}

print("Access granted!")
```

### Countdown (2:30 - 3:30)
```sona
let countdown = 10

while countdown > 0 {
    print(countdown)
    countdown = countdown - 1
}

print("Blast off! 🚀")
```

### Infinite Loop with `loop` (3:30 - 4:30)
```sona
loop {
    let answer = input("Type 'quit' to exit: ")
    if answer == "quit" {
        break
    }
    print("You typed: " + answer)
}
```

### Outro (4:30 - 5:00)
"While loops: run until condition is false. Use `loop` + `break` for infinite loops with exit condition!"

---

## Visual Notes
- Flowchart: condition check -> loop body -> back to check
- Warning icon for infinite loops
- Show condition becoming false
