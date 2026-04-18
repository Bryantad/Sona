# Mini-Episode 6.2: List Methods

## Script

### Intro (0:00 - 0:15)
"Lists come with powerful built-in methods. Let's explore them!"

### Adding Items (0:15 - 1:30)
```sona
let fruits = ["apple"]

fruits.push("banana")       // Add to end
print(fruits)  // ["apple", "banana"]

fruits.insert(0, "mango")   // Insert at position
print(fruits)  // ["mango", "apple", "banana"]
```

### Removing Items (1:30 - 2:30)
```sona
let fruits = ["apple", "banana", "cherry"]

fruits.pop()        // Remove last
print(fruits)  // ["apple", "banana"]

fruits.remove(0)    // Remove at index
print(fruits)  // ["banana"]
```

### Finding Items (2:30 - 3:30)
```sona
let colors = ["red", "green", "blue"]

print(colors.contains("green"))  // true
print(colors.contains("yellow")) // false

print(colors.indexOf("blue"))    // 2
print(colors.indexOf("yellow"))  // -1 (not found)
```

### Sorting & Reversing (3:30 - 4:30)
```sona
let numbers = [3, 1, 4, 1, 5, 9]

print(numbers.sort())     // [1, 1, 3, 4, 5, 9]
print(numbers.reverse())  // [9, 5, 4, 3, 1, 1]
```

### Outro (4:30 - 5:00)
"push, pop, insert, remove, sort, reverse - these methods make list manipulation easy!"
