# Mini-Episode 4.1: If and Else

> Making yes/no decisions in code

## Script

### Intro (0:00 - 0:15)
"If this, then that - the most basic decision in programming!"

### Basic If (0:15 - 1:15)
```sona
let temperature = 30

if temperature > 25 {
    print("It's hot! 🔥")
}
```

"The code inside `{ }` only runs when the condition is `true`."

### If/Else (1:15 - 2:30)
"What if we want to do something when it's NOT true?"

```sona
let temperature = 15

if temperature > 25 {
    print("It's hot! 🔥")
} else {
    print("It's cool 🌤️")
}
```

"One or the other - never both!"

### Else If (2:30 - 3:45)
"Multiple options:"
```sona
let temperature = 30

if temperature > 35 {
    print("It's very hot! 🥵")
} else if temperature > 25 {
    print("It's warm 🌤️")
} else if temperature > 15 {
    print("It's cool 🌥️")
} else {
    print("It's cold! 🥶")
}
```

### Nesting (3:45 - 4:30)
```sona
let age = 25
let hasTicket = true

if age >= 18 {
    if hasTicket {
        print("Welcome to the show!")
    } else {
        print("You need a ticket")
    }
} else {
    print("Must be 18+")
}
```

### Outro (4:30 - 5:00)
"If/else lets your program make decisions. Use `else if` for multiple options!"

---

## Visual Notes
- Flowchart showing if/else paths
- True path highlighted in green
- False path highlighted in red
