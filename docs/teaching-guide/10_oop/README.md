# Module 10: Object-Oriented Programming

## Overview
Object-Oriented Programming (OOP) is a way to organize code using "objects" that combine data and behavior. This module introduces classes, objects, and inheritance.

**Target Audience:** Ages 12-55, neurodivergent-friendly  
**Prerequisites:** Modules 01-09  
**Duration:** 60-75 minutes

---

## Learning Objectives
By the end of this module, you will:
- Understand what objects and classes are
- Create classes with properties and methods
- Use inheritance to extend classes
- Know when to use OOP

---

## Why OOP Matters

OOP helps you model real-world things in code:

| Real World | In Code |
|------------|---------|
| Dog | Class `Dog` |
| My dog Buddy | Object (instance) |
| Name, age, breed | Properties |
| Bark, eat, sleep | Methods |

---

## Mini-Lessons in This Module

| Mini | Topic | Focus |
|------|-------|-------|
| [mini-1](mini-1_classes.md) | Classes & Objects | Creating and using classes |
| [mini-2](mini-2_methods.md) | Methods & Self | Adding behavior to objects |
| [mini-3](mini-3_inheritance.md) | Inheritance | Extending and customizing classes |

---

## Key Vocabulary

| Term | Simple Definition | Example |
|------|-------------------|---------|
| **Class** | Blueprint for objects | `class Dog { }` |
| **Object** | Instance of a class | `let buddy = Dog()` |
| **Property** | Data stored in object | `buddy.name` |
| **Method** | Function inside a class | `buddy.bark()` |
| **Constructor** | Sets up new objects | `func init()` |
| **Inheritance** | Class based on another | `class Poodle extends Dog` |

---

## Quick Reference

```sona
// Define a class
class Dog {
    func init(name, age) {
        self.name = name
        self.age = age
    }
    
    func bark() {
        print("{self.name} says Woof!")
    }
    
    func birthday() {
        self.age = self.age + 1
    }
}

// Create objects
let buddy = Dog("Buddy", 3)
let max = Dog("Max", 5)

// Use objects
print(buddy.name)      // "Buddy"
buddy.bark()           // "Buddy says Woof!"
buddy.birthday()
print(buddy.age)       // 4
```

---

## When to Use OOP

**Use OOP when:**
- Modeling real-world things (users, products, games)
- You have data with related behavior
- You need multiple similar items
- Code reuse through inheritance helps

**Maybe skip OOP when:**
- Simple scripts with few functions
- Purely data transformation
- Performance-critical code

---

## Practice Challenges

### Challenge 1: BankAccount Class
Create a `BankAccount` class with deposit and withdraw methods.

### Challenge 2: Rectangle Class
Create a `Rectangle` class with width, height, area(), and perimeter() methods.

### Challenge 3: Game Character
Create a `Character` class with health, attack, and defend methods.

---

## Next Steps
→ Continue to [Module 11: Standard Library Deep Dive](../11_stdlib/README.md)
