# Mini-Episode 4.3: Match Expression

> A cleaner way to handle multiple choices

## Script

### Intro (0:00 - 0:15)
"When you have many options, `match` is cleaner than many if/else statements!"

### Basic Match (0:15 - 1:30)
```sona
let grade = "B"

match grade {
    "A" => print("Excellent!")
    "B" => print("Good!")
    "C" => print("Okay")
    "D" => print("Needs work")
    "F" => print("Failed")
    _ => print("Invalid grade")
}
```

"The `_` catches anything that doesn't match above."

### Compare to If/Else (1:30 - 2:30)
```sona
// This if/else chain...
if grade == "A" {
    print("Excellent!")
} else if grade == "B" {
    print("Good!")
} else if grade == "C" {
    print("Okay")
} else {
    print("Other")
}

// ...becomes this clean match!
match grade {
    "A" => print("Excellent!")
    "B" => print("Good!")
    "C" => print("Okay")
    _ => print("Other")
}
```

### Multiple Values (2:30 - 3:30)
```sona
let day = "Saturday"

match day {
    "Saturday" | "Sunday" => print("Weekend! 🎉")
    "Monday" => print("Start of week")
    "Friday" => print("Almost there!")
    _ => print("Regular day")
}
```

"Use `|` to match multiple values."

### Match with Blocks (3:30 - 4:30)
```sona
let command = "help"

match command {
    "help" => {
        print("Available commands:")
        print("- help: Show this message")
        print("- quit: Exit program")
    }
    "quit" => {
        print("Goodbye!")
    }
    _ => {
        print("Unknown command")
        print("Type 'help' for options")
    }
}
```

### Outro (4:30 - 5:00)
"Use `match` when you have many specific values to check. It's clean and easy to read!"

---

## Visual Notes
- Side-by-side comparison with if/else
- Arrow showing value matching to branch
- Highlight the `_` wildcard pattern
