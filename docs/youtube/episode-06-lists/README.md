# Episode 06: Lists 📋

> Store multiple items in one place

## Episode Overview

**Duration:** 15 minutes  
**Level:** Beginner  
**Goal:** Create, access, and modify lists

---

## Script Outline

### Intro (0:00 - 0:30)
"What if you need to store 100 names? You don't create 100 variables - you use a list!"

### Creating Lists (0:30 - 3:00)
```sona
let fruits = ["apple", "banana", "cherry"]
let numbers = [1, 2, 3, 4, 5]
let mixed = ["hello", 42, true]
let empty = []
```

### Accessing Items (3:00 - 6:00)
```sona
let fruits = ["apple", "banana", "cherry"]
print(fruits[0])   // apple (first item)
print(fruits[1])   // banana
print(fruits[-1])  // cherry (last item)
```

### Modifying Lists (6:00 - 9:00)
```sona
let fruits = ["apple", "banana"]
fruits.push("cherry")      // Add to end
fruits.insert(0, "mango")  // Add at position
fruits.remove(1)           // Remove by index
```

### List Methods (9:00 - 12:00)
```sona
let nums = [3, 1, 4, 1, 5]
print(nums.length())   // 5
print(nums.sort())     // [1, 1, 3, 4, 5]
print(nums.reverse())  // [5, 4, 3, 1, 1]
print(nums.contains(4)) // true
```

### Looping Through Lists (12:00 - 14:00)
```sona
let colors = ["red", "green", "blue"]
for color in colors {
    print("I like " + color)
}
```

### Outro (14:00 - 15:00)
- Challenge: Create a shopping list program
- Next: Dictionaries - key-value pairs

---

## Mini-Episodes
1. [mini-1: Creating Lists](mini-1_creating.md)
2. [mini-2: List Methods](mini-2_methods.md)
3. [mini-3: List Patterns](mini-3_patterns.md)
