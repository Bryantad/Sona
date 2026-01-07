# Mini-Lesson 5.1: Lists

## What is a List?

A **list** is like a container that holds multiple items in order. Think of it like:
- A shopping list
- A playlist of songs
- A row of lockers (each with a number)

---

## Creating Lists

```sona
// Empty list
let empty = []

// List with items
let numbers = [1, 2, 3, 4, 5]
let names = ["Alice", "Bob", "Charlie"]
let mixed = [1, "hello", true, 3.14]  // Can mix types
```

### Visual Representation

```
names = ["Alice", "Bob", "Charlie"]
         ↓        ↓       ↓
Index:   0        1       2
```

**Key Point:** Indexes start at 0, not 1!

---

## Accessing Items

Use square brackets `[]` with the index number:

```sona
let fruits = ["apple", "banana", "cherry"]

print(fruits[0])   // "apple"  (first)
print(fruits[1])   // "banana" (second)
print(fruits[2])   // "cherry" (third)
```

### Negative Indexes

```sona
print(fruits[-1])  // "cherry" (last item)
print(fruits[-2])  // "banana" (second to last)
```

---

## Modifying Lists

### Change an Item
```sona
let colors = ["red", "green", "blue"]
colors[1] = "yellow"
print(colors)  // ["red", "yellow", "blue"]
```

### Add Items
```sona
let list = [1, 2, 3]
list.push(4)        // Add to end: [1, 2, 3, 4]
list.insert(0, 0)   // Add at index 0: [0, 1, 2, 3, 4]
```

### Remove Items
```sona
let list = ["a", "b", "c", "d"]
list.pop()          // Remove last: ["a", "b", "c"]
list.remove("b")    // Remove by value: ["a", "c"]
```

---

## List Properties

```sona
let items = [10, 20, 30, 40, 50]

print(items.length())  // 5 (how many items)
print(items.first())   // 10
print(items.last())    // 50
```

---

## Common Patterns

### Check if Item Exists
```sona
let fruits = ["apple", "banana"]

if "apple" in fruits {
    print("Found it!")
}
```

### Get a Slice (Part of List)
```sona
let numbers = [0, 1, 2, 3, 4, 5]
let part = numbers[1:4]  // [1, 2, 3] (index 1 up to, not including, 4)
```

---

## Practice

### Exercise 1
Create a list of your 3 favorite movies. Print the second one.

### Exercise 2
Create a list `[10, 20, 30]`. Add `40` to the end, then print the whole list.

### Exercise 3
What will this print?
```sona
let letters = ["a", "b", "c", "d"]
print(letters[-1])
print(letters[0])
```

<details>
<summary>Answer</summary>

```
d
a
```
`letters[-1]` is the last item, `letters[0]` is the first.

</details>

---

## Summary

| Operation | Code | Result |
|-----------|------|--------|
| Create | `let x = [1, 2, 3]` | New list |
| Access | `x[0]` | First item |
| Last item | `x[-1]` | Last item |
| Add | `x.push(4)` | Add to end |
| Remove | `x.pop()` | Remove from end |
| Length | `x.length()` | Count of items |

---

→ Next: [mini-2: Dictionaries](mini-2_dictionaries.md)
