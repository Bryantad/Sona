# Episode 05: Loops 🔄

> Doing things repeatedly

## Episode Overview

**Duration:** 15 minutes  
**Level:** Beginner  
**Goal:** Master for loops, while loops, and loop control

---

## Script Outline

### Intro (0:00 - 0:30)
"What if you need to do something 100 times? You don't write it 100 times - you use a loop!"

### For Loops (0:30 - 4:00)
```sona
// Count 1 to 5
for i in range(1, 6) {
    print(i)
}

// Loop through a list
let fruits = ["apple", "banana", "cherry"]
for fruit in fruits {
    print(fruit)
}
```

### While Loops (4:00 - 7:00)
```sona
let count = 0
while count < 5 {
    print(count)
    count = count + 1
}
```

### Infinite Loops with Break (7:00 - 10:00)
```sona
loop {
    let answer = input("Continue? (y/n): ")
    if answer == "n" {
        break
    }
    print("Looping...")
}
```

### Continue Statement (10:00 - 12:00)
```sona
for i in range(10) {
    if i % 2 == 0 {
        continue  // Skip even numbers
    }
    print(i)  // Only prints odd: 1, 3, 5, 7, 9
}
```

### Practical Examples (12:00 - 14:00)
- Countdown timer
- Sum of numbers
- Finding items in a list

### Outro (14:00 - 15:00)
- Challenge: Create a number guessing game
- Next: Lists and collections

---

## Mini-Episodes

1. [mini-1: For Loops](mini-1_for.md) - 5 min
2. [mini-2: While Loops](mini-2_while.md) - 5 min
3. [mini-3: Break & Continue](mini-3_control.md) - 5 min

---

## Keywords
for loop, while loop, iteration, break, continue, range
