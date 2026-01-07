# Mini-Lesson 10.1: Classes & Objects

## The Cookie Cutter Analogy

Think of a **class** as a cookie cutter:
- The cookie cutter (class) defines the shape
- Each cookie (object) is made from that shape
- Each cookie can have different decorations (property values)

---

## Creating a Class

```sona
class Dog {
    func init(name, breed) {
        self.name = name
        self.breed = breed
        self.age = 0
    }
}
```

**Breaking it down:**
- `class Dog` - Declare a class named Dog
- `func init(...)` - Constructor (runs when creating object)
- `self.name = name` - Store name as a property
- `self` - Refers to "this object"

---

## Creating Objects (Instances)

```sona
let buddy = Dog("Buddy", "Golden Retriever")
let max = Dog("Max", "Poodle")
```

Now we have two separate dog objects:
- `buddy` has name "Buddy", breed "Golden Retriever"
- `max` has name "Max", breed "Poodle"

---

## Accessing Properties

Use dot notation:

```sona
print(buddy.name)   // "Buddy"
print(buddy.breed)  // "Golden Retriever"
print(max.name)     // "Max"
```

---

## Changing Properties

```sona
let car = Car("Toyota", "Red")

print(car.color)    // "Red"
car.color = "Blue"
print(car.color)    // "Blue"
```

---

## The Constructor (`init`)

The `init` method runs automatically when you create an object:

```sona
class Player {
    func init(name) {
        print("Creating player: " + name)
        self.name = name
        self.score = 0        // Default value
        self.level = 1        // Default value
        self.health = 100     // Default value
    }
}

let p1 = Player("Alex")
// Output: "Creating player: Alex"
```

---

## Default Parameter Values

```sona
class Enemy {
    func init(name, health = 100, damage = 10) {
        self.name = name
        self.health = health
        self.damage = damage
    }
}

let goblin = Enemy("Goblin", 50, 5)      // Custom values
let dragon = Enemy("Dragon", 500, 50)    // Custom values
let slime = Enemy("Slime")               // Uses defaults: 100, 10
```

---

## Objects Are Independent

Changes to one object don't affect others:

```sona
let dog1 = Dog("Buddy", "Lab")
let dog2 = Dog("Max", "Poodle")

dog1.name = "Charlie"

print(dog1.name)  // "Charlie"
print(dog2.name)  // "Max" (unchanged!)
```

---

## Real-World Example: User Account

```sona
class User {
    func init(username, email) {
        self.username = username
        self.email = email
        self.created_at = time.now()
        self.posts = []
        self.friends = []
        self.is_active = true
    }
}

let user1 = User("alice123", "alice@email.com")
let user2 = User("bob456", "bob@email.com")

print(user1.username)     // "alice123"
print(user1.is_active)    // true
user1.posts.push("Hello, world!")
```

---

## Objects in Collections

```sona
class Task {
    func init(title) {
        self.title = title
        self.done = false
    }
}

let tasks = [
    Task("Buy groceries"),
    Task("Walk the dog"),
    Task("Do homework")
]

for task in tasks {
    print("{task.title} - Done: {task.done}")
}
```

---

## Checking Object Type

```sona
let buddy = Dog("Buddy", "Lab")

print(typeof(buddy))         // "Dog"
print(buddy instanceof Dog)  // true
```

---

## Practice

### Exercise 1
Create a `Book` class with properties: title, author, pages. Create 2 book objects.

### Exercise 2
Create a `Rectangle` class with width and height. Create 3 different rectangles.

### Exercise 3
Create a `Student` class with name and grades (list). Start with empty grades list.

<details>
<summary>Exercise 1 Answer</summary>

```sona
class Book {
    func init(title, author, pages) {
        self.title = title
        self.author = author
        self.pages = pages
    }
}

let book1 = Book("1984", "George Orwell", 328)
let book2 = Book("Dune", "Frank Herbert", 412)

print(book1.title)  // "1984"
print(book2.pages)  // 412
```

</details>

---

## Summary

| Concept | Syntax | Purpose |
|---------|--------|---------|
| Class | `class Name { }` | Define blueprint |
| Constructor | `func init(...) { }` | Set up object |
| self | `self.property` | Access this object |
| Create | `let x = Name()` | Make new object |
| Access | `x.property` | Get/set values |

---

→ Next: [mini-2: Methods & Self](mini-2_methods.md)
