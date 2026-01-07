# Module 05: Collections

## Overview
Collections let you store and organize multiple pieces of data. This module covers lists, dictionaries, and how to work with groups of information.

**Target Audience:** Ages 12-55, neurodivergent-friendly  
**Prerequisites:** Modules 01-04  
**Duration:** 45-60 minutes

---

## Learning Objectives
By the end of this module, you will:
- Create and use lists to store multiple items
- Access items by their position (index)
- Create dictionaries with key-value pairs
- Loop through collections

---

## Why Collections Matter

Imagine you have 100 student names. Without collections, you'd need 100 separate variables! Collections let you store all 100 names in ONE place.

**Real-world examples:**
- A playlist (list of songs)
- A phone contacts list (names → phone numbers)
- A shopping cart (list of items)

---

## Mini-Lessons in This Module

| Mini | Topic | Focus |
|------|-------|-------|
| [mini-1](mini-1_lists.md) | Lists | Creating, accessing, modifying lists |
| [mini-2](mini-2_dictionaries.md) | Dictionaries | Key-value pairs, lookups |
| [mini-3](mini-3_iteration.md) | Iterating Collections | Looping through lists and dicts |

---

## Key Vocabulary

| Term | Simple Definition | Example |
|------|-------------------|---------|
| **List** | An ordered group of items | `[1, 2, 3]` |
| **Index** | Position number (starts at 0) | `list[0]` gets first item |
| **Dictionary** | Items stored by name (key) | `{"name": "Alex"}` |
| **Key** | The name you use to find a value | `"name"` in the example above |
| **Value** | The data stored at a key | `"Alex"` in the example above |

---

## Quick Reference

```sona
// Lists
let fruits = ["apple", "banana", "cherry"]
print(fruits[0])        // "apple" (first item)
print(fruits.length())  // 3

// Add to list
fruits.push("date")

// Dictionaries
let person = {
    "name": "Jordan",
    "age": 25
}
print(person["name"])   // "Jordan"
print(person.name)      // Also "Jordan" (dot notation)
```

---

## Common Mistakes

❌ **Forgetting indexes start at 0**
```sona
let colors = ["red", "blue", "green"]
print(colors[1])  // This is "blue", not "red"!
```

✅ **Remember: First item is at index 0**
```sona
print(colors[0])  // "red" - the first item
```

---

## Practice Challenges

### Challenge 1: Favorite Things
Create a list of your 5 favorite foods. Print the first and last items.

### Challenge 2: Student Info
Create a dictionary with your name, age, and favorite color. Print each value.

### Challenge 3: Class Roster
Create a list of 3 student names. Use a loop to print "Hello, [name]!" for each.

---

## Self-Check Questions

1. What index gets the FIRST item in a list?
2. What's the difference between a list and a dictionary?
3. How do you add a new item to a list?

<details>
<summary>Answers</summary>

1. Index `0` (zero)
2. Lists use number positions (0, 1, 2...), dictionaries use named keys
3. Use `.push(item)` or `.append(item)`

</details>

---

## Next Steps
→ Continue to [Module 06: String Operations](../06_strings/README.md)
