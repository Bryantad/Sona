# Mini-Episode 6.1: Creating Lists

## Script

### Intro (0:00 - 0:15)
"Lists let you store multiple items together. Let's learn how to create them!"

### Basic Lists (0:15 - 1:30)
```sona
// A list of strings
let fruits = ["apple", "banana", "cherry"]

// A list of numbers
let scores = [95, 87, 92, 78, 88]

// An empty list
let todoList = []
```

### Accessing Items (1:30 - 2:45)
```sona
let colors = ["red", "green", "blue", "yellow"]

print(colors[0])   // "red" - first item
print(colors[1])   // "green" - second item
print(colors[-1])  // "yellow" - last item
print(colors[-2])  // "blue" - second to last
```

### Slicing (2:45 - 3:45)
```sona
let numbers = [0, 1, 2, 3, 4, 5]

print(numbers[1:4])   // [1, 2, 3]
print(numbers[:3])    // [0, 1, 2]
print(numbers[3:])    // [3, 4, 5]
```

### List Length (3:45 - 4:30)
```sona
let items = ["a", "b", "c", "d"]
print(items.length())  // 4

if items.length() > 0 {
    print("List is not empty!")
}
```

### Outro (4:30 - 5:00)
"Lists store ordered collections. Use index [0] for first item, [-1] for last!"
