# Mini-Episode 5.1: For Loops

> Repeat a known number of times

## Script

### Intro (0:00 - 0:15)
"For loops are perfect when you know how many times to repeat!"

### Basic For Loop (0:15 - 1:30)
```sona
for i in range(5) {
    print(i)
}
// Output: 0, 1, 2, 3, 4
```

"Range gives you numbers from 0 up to (but not including) 5."

### Custom Range (1:30 - 2:30)
```sona
// Start at 1, go to 5
for i in range(1, 6) {
    print(i)
}
// Output: 1, 2, 3, 4, 5

// Count by 2s
for i in range(0, 10, 2) {
    print(i)
}
// Output: 0, 2, 4, 6, 8
```

### Looping Through Lists (2:30 - 3:30)
```sona
let colors = ["red", "green", "blue"]

for color in colors {
    print("I like " + color)
}
```

### With Index (3:30 - 4:30)
```sona
let fruits = ["apple", "banana", "cherry"]

for i, fruit in enumerate(fruits) {
    print(str(i + 1) + ". " + fruit)
}
// Output:
// 1. apple
// 2. banana
// 3. cherry
```

### Outro (4:30 - 5:00)
"For loops: perfect for lists and counting. Use `range()` for numbers, loop directly over lists!"

---

## Visual Notes
- Animation showing loop iteration
- Number line for range()
- List items being visited one by one
