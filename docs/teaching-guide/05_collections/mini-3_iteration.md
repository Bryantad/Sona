# Mini-Lesson 5.3: Iterating Collections

## What is Iteration?

**Iteration** means going through each item in a collection, one by one. It's like:
- Reading each book on a shelf
- Checking each item off a list
- Looking at each photo in an album

---

## Looping Through Lists

### Basic For Loop

```sona
let fruits = ["apple", "banana", "cherry"]

for fruit in fruits {
    print(fruit)
}
```

**Output:**
```
apple
banana
cherry
```

The variable `fruit` takes on each value in the list, one at a time.

---

## Getting Index AND Value

Sometimes you need to know the position:

```sona
let colors = ["red", "green", "blue"]

for i, color in enumerate(colors) {
    print(i + ": " + color)
}
```

**Output:**
```
0: red
1: green
2: blue
```

---

## Looping Through Dictionaries

### Loop Through Keys

```sona
let ages = {
    "Alice": 25,
    "Bob": 30,
    "Carol": 28
}

for name in ages.keys() {
    print(name)
}
```

**Output:**
```
Alice
Bob
Carol
```

### Loop Through Values

```sona
for age in ages.values() {
    print(age)
}
```

**Output:**
```
25
30
28
```

### Loop Through Both (Key and Value)

```sona
for name, age in ages.items() {
    print(name + " is " + age + " years old")
}
```

**Output:**
```
Alice is 25 years old
Bob is 30 years old
Carol is 28 years old
```

---

## Common Iteration Patterns

### Pattern 1: Find Something

```sona
let numbers = [4, 8, 15, 16, 23, 42]
let target = 15
let found = false

for num in numbers {
    if num == target {
        found = true
        print("Found " + target + "!")
        break  // Stop searching
    }
}

if not found {
    print("Not found")
}
```

### Pattern 2: Count Things

```sona
let grades = [85, 92, 78, 95, 88, 76]
let count = 0

for grade in grades {
    if grade >= 90 {
        count = count + 1
    }
}

print("A grades: " + count)  // "A grades: 2"
```

### Pattern 3: Transform Each Item

```sona
let numbers = [1, 2, 3, 4, 5]
let doubled = []

for num in numbers {
    doubled.push(num * 2)
}

print(doubled)  // [2, 4, 6, 8, 10]
```

### Pattern 4: Sum All Items

```sona
let prices = [10.99, 5.50, 3.25, 8.00]
let total = 0

for price in prices {
    total = total + price
}

print("Total: $" + total)  // "Total: $27.74"
```

---

## Using `repeat` for Simple Counting

When you just need to do something N times:

```sona
repeat 5 {
    print("Hello!")
}
```

This prints "Hello!" five times.

---

## Nested Loops

Loop inside a loop—useful for grids and combinations:

```sona
let rows = ["A", "B", "C"]
let cols = [1, 2, 3]

for row in rows {
    for col in cols {
        print(row + col)  // A1, A2, A3, B1, B2, ...
    }
}
```

**Visual:**
```
A1  A2  A3
B1  B2  B3
C1  C2  C3
```

---

## Practice

### Exercise 1
Loop through this list and print each item in uppercase:
```sona
let words = ["hello", "world", "sona"]
```

### Exercise 2
Create a dictionary of 3 friends and their favorite colors. Loop through and print "[Friend]'s favorite color is [color]".

### Exercise 3
Using a loop, calculate the sum of `[10, 20, 30, 40, 50]`.

<details>
<summary>Exercise 3 Answer</summary>

```sona
let numbers = [10, 20, 30, 40, 50]
let sum = 0

for num in numbers {
    sum = sum + num
}

print(sum)  // 150
```

</details>

---

## Summary

| Collection | Loop Syntax | What You Get |
|------------|-------------|--------------|
| List | `for item in list` | Each value |
| List with index | `for i, item in enumerate(list)` | Index and value |
| Dict keys | `for key in dict.keys()` | Each key |
| Dict values | `for val in dict.values()` | Each value |
| Dict both | `for k, v in dict.items()` | Key and value |

---

## Module 05 Complete! 🎉

You've learned:
- ✅ Lists (ordered collections)
- ✅ Dictionaries (named key-value pairs)
- ✅ Iterating through both

→ Next: [Module 06: String Operations](../06_strings/README.md)
