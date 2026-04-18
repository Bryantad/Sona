# Mini-Episode 2.1: Variables Explained

> Understanding how to store data in your programs

## Script

### Intro (0:00 - 0:15)
"Variables are the most important concept in programming. Let's understand them!"

### The Box Analogy (0:15 - 1:30)
"Imagine a labeled box:
- The label is the variable NAME
- What's inside is the VALUE

```sona
let age = 15
```

- `let` = 'create a new box'
- `age` = the label on the box
- `=` = 'put this inside'
- `15` = what goes in the box"

### Creating Variables (1:30 - 2:30)
```sona
// Creating variables
let name = "Alex"
let score = 100
let isHappy = true

// Using them
print(name)    // Alex
print(score)   // 100
print(isHappy) // true
```

### Changing Values (2:30 - 3:30)
"The box keeps the same label, but contents can change:"

```sona
let score = 0
print(score)  // 0

score = 10    // No 'let' - box already exists!
print(score)  // 10

score = score + 5  // Use current value in calculation
print(score)  // 15
```

### Naming Rules (3:30 - 4:30)
"Good names:
- `age`, `userName`, `totalScore`

Bad names:
- `x`, `thing`, `123abc` (can't start with number)"

```sona
// Good - descriptive names
let playerName = "Hero"
let playerHealth = 100

// Bad - unclear names
let x = "Hero"
let n = 100
```

### Outro (4:30 - 5:00)
"Variables hold your data. Give them clear names! Next: let's look at different types of data."

---

## Visual Notes
- Show box animation with label and contents
- Highlight the parts of variable declaration
- Show value changing inside the same box
